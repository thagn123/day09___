import json
import sys
from mcp_server import dispatch_tool, list_tools

def clear_screen():
    print("\033[H\033[J", end="")

def main():
    while True:
        clear_screen()
        print("="*60)
        print("🛠️  Interactive MCP Tool Tester")
        print("="*60)
        
        tools = list_tools()
        print("\nAvailable Tools:")
        for idx, tool in enumerate(tools, 1):
            print(f"  {idx}. {tool['name']}: {tool['description']}")
        
        print("\n  0. Exit")
        
        choice = input("\nSelect a tool number (or 0 to exit): ")
        if choice == '0':
            break
            
        try:
            tool_idx = int(choice) - 1
            if tool_idx < 0 or tool_idx >= len(tools):
                print("❌ Invalid choice.")
                input("\nPress Enter to continue...")
                continue
            
            selected_tool = tools[tool_idx]
            tool_name = selected_tool['name']
            schema = selected_tool['inputSchema']
            
            print(f"\n--- Testing Tool: {tool_name} ---")
            print(f"Description: {selected_tool['description']}")
            print("Required arguments:", schema.get('required', []))
            
            # Interactive input for each property
            tool_input = {}
            properties = schema.get('properties', {})
            for prop, details in properties.items():
                is_required = prop in schema.get('required', [])
                req_str = "(required)" if is_required else "(optional)"
                default = details.get('default', '')
                
                val = input(f"  Enter value for {prop} {req_str} [{default}]: ").strip()
                
                if not val and is_required:
                    if default != '':
                        val = default
                    else:
                        print(f"❌ Property {prop} is required.")
                        break
                
                if val:
                    # Basic type conversion
                    if details.get('type') == 'integer':
                        try:
                            val = int(val)
                        except ValueError:
                            print(f"❌ {prop} must be an integer.")
                            break
                    elif details.get('type') == 'boolean':
                        val = val.lower() in ['true', '1', 'yes', 'y']
                    
                    tool_input[prop] = val
            else:
                # Successfully collected all inputs
                print("\nCalling tool with input:", json.dumps(tool_input, indent=2))
                result = dispatch_tool(tool_name, tool_input)
                
                print("\n" + "="*20 + " RESULT " + "="*20)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print("="*48)
                input("\nPress Enter for next test...")
                
        except ValueError:
            print("❌ Please enter a number.")
            input("\nPress Enter to continue...")
            
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
