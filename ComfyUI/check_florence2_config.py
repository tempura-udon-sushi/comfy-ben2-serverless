import json

workflow_path = r"C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\user\default\workflows\BG_remove_BEN2_simple.json"

with open(workflow_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print("=" * 70)
print("Florence2 Configuration Analysis")
print("=" * 70)

for node in workflow['nodes']:
    if 'Florence2' in node['type']:
        print(f"\n{node['type']} (Node {node['id']}):")
        print(f"  Widget values: {node.get('widgets_values', [])}")
        print(f"  Inputs:")
        for inp in node.get('inputs', []):
            print(f"    - {inp['name']}: {inp.get('type', 'unknown')}")

print("\n" + "=" * 70)
print("Florence2 Optimization Recommendations")
print("=" * 70)
print("""
For SAFETY CHECK workflows, you can optimize Florence2 speed:

1. **Model Size** (Current: ?)
   - base: Faster, good enough for safety detection
   - large: Slower, more detailed (may be overkill for safety)
   
2. **Task Type** (Check your Florence2Run settings)
   - 'caption': Basic caption (FASTEST)
   - 'detailed caption': More detailed (SLOWER)
   - 'more detailed caption': Very detailed (SLOWEST)
   
   For SAFETY checks, you only need basic caption!

3. **Max Tokens** (if configurable)
   - Lower = faster (e.g., 128-256 tokens sufficient for safety)
   - Higher = slower but more detailed

4. **Resolution** 
   - Florence2 resizes internally, but smaller input = faster

RECOMMENDATION FOR SAFETY WORKFLOW:
- Use 'base' model (not 'large')
- Use 'caption' task (not 'detailed caption')
- This should reduce 10sec → ~3-5sec on RTX 3080 Ti
""")
print("=" * 70)
