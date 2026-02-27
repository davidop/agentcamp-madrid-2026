#!/usr/bin/env python3
"""
Simple script to validate Mermaid syntax by extracting and checking basic syntax patterns.
"""

import re
import sys

def validate_mermaid_syntax(file_path):
    """Extract and validate Mermaid chart syntax from markdown file."""
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract Mermaid code blocks
        mermaid_pattern = r'```mermaid\n(.*?)\n```'
        mermaid_blocks = re.findall(mermaid_pattern, content, re.DOTALL)
        
        if not mermaid_blocks:
            print("❌ No Mermaid chart found in the file")
            return False
        
        print(f"✅ Found {len(mermaid_blocks)} Mermaid chart(s)")
        
        for i, block in enumerate(mermaid_blocks):
            print(f"\n🔍 Validating Mermaid chart {i+1}:")
            
            # Basic syntax validation
            lines = block.strip().split('\n')
            
            # Check for graph/diagram declaration
            graph_declaration = False
            diagram_type = None
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('graph '):
                    graph_declaration = True
                    diagram_type = 'graph'
                    print(f"  ✅ Graph declaration found: {stripped}")
                    break
                elif stripped.startswith('sequenceDiagram'):
                    graph_declaration = True
                    diagram_type = 'sequence'
                    print(f"  ✅ Sequence diagram declaration found")
                    break
                elif stripped.startswith('flowchart'):
                    graph_declaration = True
                    diagram_type = 'flowchart'
                    print(f"  ✅ Flowchart declaration found: {stripped}")
                    break
            
            if not graph_declaration:
                print("  ❌ No graph/diagram declaration found")
                return False
            
            # Count nodes and connections (only for graph/flowchart types)
            if diagram_type in ('graph', 'flowchart'):
                nodes = []
                connections = []
                
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith('%%') or line.startswith('classDef') or line.startswith('class ') or line.startswith('style '):
                        continue
                    
                    # Look for node definitions
                    node_pattern = r'(\w+)\[(.*?)\]'
                    node_matches = re.findall(node_pattern, line)
                    for match in node_matches:
                        if match[0] not in nodes:
                            nodes.append(match[0])
                    
                    # Look for connections
                    connection_patterns = [
                        r'(\w+)\s*-->\s*(\w+)',  # -->
                        r'(\w+)\s*-\.->\s*(\w+)', # -.->
                        r'(\w+)\s*<---->\s*(\w+)' # <---->
                    ]
                    
                    for pattern in connection_patterns:
                        conn_matches = re.findall(pattern, line)
                        connections.extend(conn_matches)
                
                print(f"  📊 Found {len(nodes)} nodes: {', '.join(nodes)}")
                print(f"  🔗 Found {len(connections)} connections")
                
                # Validate that connections reference valid nodes
                valid_connections = True
                for conn in connections:
                    if conn[0] not in nodes or conn[1] not in nodes:
                        print(f"  ❌ Invalid connection: {conn[0]} -> {conn[1]}")
                        valid_connections = False
                
                if valid_connections:
                    print(f"  ✅ All connections are valid")
            else:
                print(f"  ℹ️  {diagram_type} diagram — skipping node/connection validation")
            
            # Check for styling
            has_styling = any('classDef' in line for line in lines)
            if has_styling:
                print(f"  🎨 Chart includes styling definitions")
            
        return True
        
    except Exception as e:
        print(f"❌ Error validating file: {e}")
        return False

def main():
    """Main validation function."""
    
    # Find the latest generated file
    import os
    import glob
    
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    
    pattern = os.path.join(docs_dir, "SolutionOverview-*.md")
    files = glob.glob(pattern)
    
    if not files:
        print("❌ No generated documentation files found")
        return False
    
    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)
    print(f"🔍 Validating latest generated file: {os.path.basename(latest_file)}")
    
    return validate_mermaid_syntax(latest_file)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)