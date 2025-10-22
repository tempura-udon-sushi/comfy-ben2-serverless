Awesome — here’s the **build-ready Windsurf task pack** for the lean (no-ads) model. It’s structured as bite-size tasks you can drop into branches or tickets, with code skeletons you can paste directly.

---

# SimplyPNG – Lean Monetization Build Spec

**Stack**: Next.js (App Router) + TypeScript + Supabase (Auth, DB, Edge Functions) + Stripe Checkout + Vercel
**Scopes**: Credits engine, bonus flows (email, share), referral, purchase packs, webhooks, analytics

---

## 0) Repo Setup

**Tasks**

1. Add envs:

   ```
   NEXT_PUBLIC_SUPABASE_URL=
   NEXT_PUBLIC_SUPABASE_ANON_KEY=
   SUPABASE_SERVICE_ROLE_KEY=
   STRIPE_SECRET_KEY=
   STRIPE_WEBHOOK_SECRET=
   NEXT_PUBLIC_APP_URL=https://simplypng.com
   ```
2. Install:

   ```bash
   pnpm add @supabase/supabase-js stripe zod nanoid
   pnpm add -D @types/node @types/jsonwebtoken
   ```

---

## 1) Database & Security (Supabase)

**SQL: tables**

```sql
-- 1) profiles
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  claimed_bonus boolean not null default false,
  ref_code text unique,
  referrer_id uuid references public.profiles(id) on delete set null,
  created_at timestamp with time zone default now()
);

-- 2) user_credits
create table if not exists public.user_credits (
  user_id uuid primary key references auth.users(id) on delete cascade,
  credits integer not null default 0,
  share_last_claim timestamp with time zone,
  updated_at timestamp with time zone default now()
);

-- 3) purchases
create table if not exists public.purchases (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  pack_code text not null, -- e.g. PACK_40, PACK_100
  stripe_session_id text unique,
  created_at timestamp with time zone default now()
);
```

**RLS & Policies**

```sql
alter table public.profiles enable row level security;
alter table public.user_credits enable row level security;
alter table public.purchases enable row level security;

-- Read own records
create policy "profiles_self" on public.profiles
for select using ( auth.uid() = id );
create policy "user_credits_self" on public.user_credits
for select using ( auth.uid() = user_id );
create policy "purchases_self" on public.purchases
for select using ( auth.uid() = user_id );

-- Service role only for mutations (credits add/subtract)
create policy "user_credits_no_client_write" on public.user_credits
for all using (false) with check (false);
create policy "profiles_no_client_write" on public.profiles
for all using (false) with check (false);
create policy "purchases_insert_service" on public.purchases
for insert with check (auth.role() = 'service_role');
```

**Seed (optional)**

```sql
-- generate a ref_code on profile creation (Edge function also OK)
create extension if not exists pgcrypto;
create or replace function public.ensure_user_credit_row()
returns trigger as $$
begin
  insert into public.user_credits(user_id, credits)
  values (new.id, 0) on conflict do nothing;
  if new.ref_code is null then
    new.ref_code := encode(gen_random_bytes(6), 'hex');
  end if;
  return new;
end; $$ language plpgsql;

drop trigger if exists trg_profiles_bootstrap on public.profiles;
create trigger trg_profiles_bootstrap
before insert on public.profiles
for each row execute function public.ensure_user_credit_row();
```

---

## 2) Supabase Service Helpers (Server-only)

`/lib/supabaseAdmin.ts`

```ts
import { createClient } from '@supabase/supabase-js';

export const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!, // SERVER ONLY
  { auth: { persistSession: false } }
);
```

---

## 3) Credits Engine (Edge Functions or Route Handlers)

**Contract**

* `decrementCredit(userId: string)` – throws if insufficient
* `addCredits(userId: string, amount: number)`
* All mutations via **service role** only.

`/lib/credits.ts`

```ts
import { supabaseAdmin } from './supabaseAdmin';

export async function addCredits(userId: string, amount: number) {
  const { data, error } = await supabaseAdmin.rpc('add_credits', {
    p_user_id: userId,
    p_amount: amount
  });
  if (error) throw error;
  return data;
}

export async function decrementCredit(userId: string) {
  const { data, error } = await supabaseAdmin.rpc('decrement_credit', { p_user_id: userId });
  if (error) throw error;
  return data;
}
```

**SQL RPCs**

```sql
create or replace function public.add_credits(p_user_id uuid, p_amount int)
returns int as $$
declare new_balance int;
begin
  update public.user_credits
  set credits = credits + p_amount, updated_at = now()
  where user_id = p_user_id
  returning credits into new_balance;

  if not found then
    insert into public.user_credits(user_id, credits)
    values (p_user_id, greatest(0, p_amount))
    returning credits into new_balance;
  end if;

  return new_balance;
end; $$ language plpgsql security definer;

create or replace function public.decrement_credit(p_user_id uuid)
returns int as $$
declare new_balance int;
begin
  update public.user_credits
  set credits = credits - 1, updated_at = now()
  where user_id = p_user_id and credits > 0
  returning credits into new_balance;

  if not found then
    raise exception 'INSUFFICIENT_CREDITS';
  end if;

  return new_balance;
end; $$ language plpgsql security definer;
```

> **Note**: `security definer` + RLS ensures only server calls via service role can mutate.

---

## 4) Purchase Packs (Stripe Checkout)

**Pack map**

```ts
// /config/packs.ts
export const CREDIT_PACKS = {
  PACK_40: { priceId: 'price_XXX_40', credits: 40, display: '$2.98' },
  PACK_100: { priceId: 'price_XXX_100', credits: 100, display: '$6.98' },
  PACK_200: { priceId: 'price_XXX_200', credits: 200, display: '$9.98' },
} as const;
```

**Create Checkout Session**

```ts
// /app/api/checkout/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { z } from 'zod';
import { CREDIT_PACKS } from '@/config/packs';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-06-20' });

const Body = z.object({ pack: z.enum(['PACK_40','PACK_100','PACK_200']), userId: z.string().uuid() });

export async function POST(req: NextRequest) {
  const json = await req.json();
  const { pack, userId } = Body.parse(json);
  const priceId = CREDIT_PACKS[pack].priceId;

  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${process.env.NEXT_PUBLIC_APP_URL}/purchase/success`,
    cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/purchase/cancel`,
    metadata: { userId, pack },
  });

  return NextResponse.json({ url: session.url });
}
```

**Webhook (grant credits)**

```ts
// /app/api/stripe/webhook/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { supabaseAdmin } from '@/lib/supabaseAdmin';
import { CREDIT_PACKS } from '@/config/packs';

export async function POST(req: NextRequest) {
  const sig = req.headers.get('stripe-signature')!;
  const raw = await req.text();
  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2024-06-20' });

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(raw, sig, process.env.STRIPE_WEBHOOK_SECRET!);
  } catch (err: any) {
    return new NextResponse(`Webhook Error: ${err.message}`, { status: 400 });
  }

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object as Stripe.Checkout.Session;
    const userId = session.metadata?.userId!;
    const pack = session.metadata?.pack as keyof typeof CREDIT_PACKS;
    const credits = CREDIT_PACKS[pack].credits;

    // idempotency guard using session id
    const { data: existed } = await supabaseAdmin
      .from('purchases').select('id').eq('stripe_session_id', session.id).maybeSingle();

    if (!existed) {
      await supabaseAdmin.from('purchases').insert({
        user_id: userId,
        pack_code: pack,
        stripe_session_id: session.id
      });
      await supabaseAdmin.rpc('add_credits', { p_user_id: userId, p_amount: credits });
    }
  }

  return NextResponse.json({ received: true });
}
```

---

## 5) Bonus: Email Signup (+5 credits)

**API route**

```ts
// /app/api/bonus/email/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseAdmin';
import { z } from 'zod';

const Body = z.object({ userId: z.string().uuid() });

export async function POST(req: NextRequest) {
  const { userId } = Body.parse(await req.json());

  const { data: profile } = await supabaseAdmin
    .from('profiles').select('claimed_bonus').eq('id', userId).single();

  if (profile?.claimed_bonus) {
    return NextResponse.json({ ok: false, reason: 'already_claimed' }, { status: 409 });
  }

  await supabaseAdmin.rpc('add_credits', { p_user_id: userId, p_amount: 5 });
  await supabaseAdmin.from('profiles').update({ claimed_bonus: true }).eq('id', userId);

  return NextResponse.json({ ok: true, added: 5 });
}
```

**UI trigger**: call after `auth.onAuthStateChange(’SIGNED_IN’)`.

---

## 6) Bonus: Social Share (+1 credit, cooldown)

**API route**

```ts
// /app/api/bonus/share/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseAdmin';
import { z } from 'zod';

const Body = z.object({ userId: z.string().uuid() });

export async function POST(req: NextRequest) {
  const { userId } = Body.parse(await req.json());
  const now = new Date();

  const { data: row } = await supabaseAdmin
    .from('user_credits').select('share_last_claim').eq('user_id', userId).single();

  const last = row?.share_last_claim ? new Date(row.share_last_claim) : null;
  const canClaim = !last || (now.getTime() - last.getTime()) / 36e5 >= 12; // every 12h

  if (!canClaim) return NextResponse.json({ ok: false, reason: 'cooldown' }, { status: 429 });

  await supabaseAdmin.rpc('add_credits', { p_user_id: userId, p_amount: 1 });
  await supabaseAdmin.from('user_credits')
    .update({ share_last_claim: now.toISOString() })
    .eq('user_id', userId);

  return NextResponse.json({ ok: true, added: 1 });
}
```

**UI tip**: Show native share dialog + “Claim” button. Credit after click (not after verified post) to keep UX simple; the cooldown limits abuse.

---

## 7) Referral (+5 for referrer, +2 for new user)

**Capture `?ref=` at signup**

```ts
// /app/(auth)/callback/page.tsx  (example)
'use client';
import { useSearchParams } from 'next/navigation';
import { useEffect } from 'react';
import { claimReferral } from '@/lib/referral';

export default function Callback() {
  const params = useSearchParams();
  useEffect(() => {
    const ref = params.get('ref');
    if (ref) claimReferral(ref); // stores in localStorage or passes to server on sign-up
  }, [params]);
  return null;
}
```

**Server action (on new user creation)**

```ts
// /lib/referral.ts
import { supabaseAdmin } from './supabaseAdmin';

export async function applyReferral(newUserId: string, refCode?: string) {
  if (!refCode) return;
  const { data: refProfile } = await supabaseAdmin
    .from('profiles').select('id').eq('ref_code', refCode).single();
  if (!refProfile) return;

  // set referrer_id on new profile
  await supabaseAdmin.from('profiles')
    .update({ referrer_id: refProfile.id })
    .eq('id', newUserId);

  // credits
  await supabaseAdmin.rpc('add_credits', { p_user_id: refProfile.id, p_amount: 5 });
  await supabaseAdmin.rpc('add_credits', { p_user_id: newUserId, p_amount: 2 });
}
```

> Hook `applyReferral` right after you create `profiles` row for a new user.

---

## 8) Processing Guard (Deduct 1 credit per edit)

**Server route before processing**

```ts
// /app/api/process/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { decrementCredit } from '@/lib/credits';
import { z } from 'zod';

const Body = z.object({ userId: z.string().uuid(), imageUrl: z.string().url() });

export async function POST(req: NextRequest) {
  const { userId, imageUrl } = Body.parse(await req.json());

  try {
    await decrementCredit(userId);
  } catch (e: any) {
    if (e.message?.includes('INSUFFICIENT_CREDITS')) {
      return NextResponse.json({ ok: false, reason: 'no_credits' }, { status: 402 });
    }
    throw e;
  }

  // … call your worker / model, return processed URL …
  const resultUrl = await processImage(imageUrl); // implement
  return NextResponse.json({ ok: true, resultUrl });
}
```

---

## 9) UI Components

**Credit Meter**

```tsx
// /components/CreditMeter.tsx
'use client';
import { useEffect, useState } from 'react';

export function CreditMeter({ initial }: { initial?: number }) {
  const [credits, setCredits] = useState<number>(initial ?? 0);
  useEffect(() => {
    // poll or swr to fetch latest credits
  }, []);
  return (
    <div className="rounded-xl border p-2 flex items-center gap-2">
      <span className="text-sm opacity-70">Credits</span>
      <span className="font-semibold">{credits}</span>
    </div>
  );
}
```

**Purchase Modal** (open, select pack, POST `/api/checkout`)

```tsx
// /components/PurchaseModal.tsx
'use client';
import { CREDIT_PACKS } from '@/config/packs'; // export a client-safe map of keys/labels only
export function PurchaseModal({ userId }: { userId: string }) {
  async function buy(pack: 'PACK_40'|'PACK_100'|'PACK_200') {
    const r = await fetch('/api/checkout', { method: 'POST', body: JSON.stringify({ pack, userId }) });
    const { url } = await r.json(); window.location.href = url;
  }
  return (
    <div>{Object.keys(CREDIT_PACKS).map((k) =>
      <button key={k} onClick={()=>buy(k as any)} className="btn">{k}</button>
    )}</div>
  );
}
```

**Bonus CTA**

```tsx
// /components/BonusCta.tsx
'use client';
export function BonusCta({ userId }: { userId: string }) {
  return (
    <div className="flex gap-2">
      <button onClick={async ()=>{
        await fetch('/api/bonus/email', { method:'POST', body: JSON.stringify({ userId })});
      }}>Claim Email Bonus</button>
      <button onClick={async ()=>{
        // (1) open share
        const shareUrl = `${location.origin}?ref=YOUR_REF_CODE`; // replace with actual
        window.open(`https://twitter.com/intent/tweet?text=Try%20SimplyPNG&url=${encodeURIComponent(shareUrl)}`);
        // (2) claim
        await fetch('/api/bonus/share', { method:'POST', body: JSON.stringify({ userId })});
      }}>Share & +1</button>
    </div>
  );
}
```

---

## 10) Analytics (minimal)

Track **events**: `edit_started`, `edit_success`, `credit_insufficient`, `bonus_claimed`, `referral_applied`, `purchase_started`, `purchase_succeeded`.
Start with a simple Postgres table or add Tinybird/Google Analytics later.

---

## 11) Guardrails & Abuse Prevention

* **Cooldown** for share bonus (12h).
* **Email bonus**: single flag `claimed_bonus`.
* **Server-side mutations only** via service role & RPC (clients cannot change credits directly).
* **Webhook idempotency** using `stripe_session_id`.
* **Rate limit** processing route (e.g., 10 req/min per user) using in-memory or Upstash.

---

## 12) Test Plan (Windsurf)

1. **DB**: create profile → auto user_credits row → ref_code generated.
2. **Credits**: `add_credits` → `decrement_credit` happy path; insufficient path raises error.
3. **Email bonus**: first claim OK, second claim 409.
4. **Share bonus**: claim OK, second claim within 12h returns 429.
5. **Referral**: `applyReferral` grants +5/+2; duplicate referral ignored.
6. **Purchase**: Checkout creates session → webhook grants credits → idempotent on retry.

---

## 13) Rollout Order (1-sprint)

1. DB & RPC, admin client (½ day)
2. Purchase flow + webhook (1 day)
3. Email bonus (½ day)
4. Share bonus (½ day)
5. Referral (1 day)
6. Guardrails + basic UI polish + tests (1 day)

---

### That’s it.

If you want, I can turn this into a **copy-pasteable Windsurf task list** (e.g., `// TASK:` comments per file + checklists), or tailor the RPCs to **Supabase Edge Functions** if you prefer keeping logic outside SQL.
