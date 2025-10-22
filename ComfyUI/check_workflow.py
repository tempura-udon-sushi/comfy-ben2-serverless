import json

with open('user/default/workflows/qwen_image_edit_dynamic_text_tesing_formatted.json') as f:
    data = json.load(f)

# Find TextEncodeQwenImageEdit nodes
for node in data['nodes']:
    if 'TextEncodeQwenImageEdit' in node['type']:
        print(f"\n=== Node ID: {node['id']} - Type: {node['type']} ===")
        print(f"Inputs:")
        for inp in node.get('inputs', []):
            print(f"  - {inp['name']} ({inp['type']})")
        print(f"Widgets: {node.get('widgets_values', [])}")
