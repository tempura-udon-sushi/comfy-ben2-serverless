import json
import sys

# Load the workflow
workflow_path = r"C:\Users\genfp\AI_avatar\Comfy_vanila\ComfyUI\user\default\workflows\BG_remove_BEN2_simple.json"

with open(workflow_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Extract node types and their connections
print("=" * 60)
print("BEN2 Workflow Structure Analysis")
print("=" * 60)
print("\nNodes in workflow:")
print("-" * 60)

nodes = {node['id']: node for node in workflow['nodes']}

for node in workflow['nodes']:
    node_id = node['id']
    node_type = node['type']
    print(f"Node {node_id}: {node_type}")

print("\n" + "=" * 60)
print("Checking for required safety check nodes:")
print("=" * 60)

required_nodes = [
    "LoadImage",
    "Florence2Image2Prompt",
    "LocalJSONExtractor",
    "ImageSafetyGate",
    "SmartResizeForModel",
    "BEN2_ONNX_RemoveBg",
    "RestoreOriginalSize",
    "SaveImage"
]

found_nodes = {}
for node in workflow['nodes']:
    node_type = node['type']
    if node_type in required_nodes:
        found_nodes[node_type] = node['id']

print("\n✓ = Found | ✗ = Missing")
for required in required_nodes:
    status = "✓" if required in found_nodes else "✗"
    node_id = f" (Node {found_nodes[required]})" if required in found_nodes else ""
    print(f"{status} {required}{node_id}")

print("\n" + "=" * 60)
print("Workflow Flow Check:")
print("=" * 60)

if "ImageSafetyGate" in found_nodes:
    safety_node = nodes[found_nodes["ImageSafetyGate"]]
    print(f"\nImageSafetyGate (Node {safety_node['id']}):")
    print("  Inputs:")
    for inp in safety_node.get('inputs', []):
        link_info = f" <- Link {inp['link']}" if inp.get('link') else " (not connected)"
        print(f"    - {inp['name']} ({inp['type']}){link_info}")
    print("  Outputs:")
    for out in safety_node.get('outputs', []):
        links = out.get('links', [])
        link_info = f" -> Links {links}" if links else " (not connected)"
        print(f"    - {out['name']} ({out['type']}){link_info}")

print("\n" + "=" * 60)
print("Expected Flow:")
print("=" * 60)
print("""
1. LoadImage
2. Florence2Image2Prompt (analyzes image)
3. LocalJSONExtractor (gets safety flags)
4. ImageSafetyGate (IMAGE + JSON → validates → outputs IMAGE)
5. SmartResizeForModel (receives IMAGE from safety gate)
6. BEN2_ONNX_RemoveBg
7. RestoreOriginalSize
8. FreeVRAMInline
9. SaveImage
""")

print("=" * 60)
if all(node in found_nodes for node in required_nodes):
    print("✅ All required nodes are present!")
else:
    print("⚠️ Some required nodes are missing!")
print("=" * 60)
