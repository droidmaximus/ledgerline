#!/usr/bin/env python3
"""
Simple document query script for PageIndex system
Usage: python query-document.py <doc_id> "<question>"
"""
import sys
import json
import requests

def query_document(doc_id: str, question: str):
    """Query a document by fetching its tree and searching for relevant information."""
    
    # Step 1: Fetch document tree from cache
    print(f"🔍 Fetching document tree for {doc_id}...")
    cache_url = f"http://localhost:8082/cache/tree/{doc_id}"
    
    try:
        response = requests.get(cache_url)
        response.raise_for_status()
        tree = response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching tree: {e}")
        return
    
    # Step 2: Display document info
    print(f"\n📄 Document: {tree.get('title', 'Unknown')}")
    print(f"📊 Pages: {tree.get('start_index', 1)} - {tree.get('end_index', 1)}")
    print(f"📝 Summary: {tree.get('summary', 'N/A')}\n")
    
    # Step 3: Search through tree structure
    print(f"💭 Question: {question}\n")
    print("🌳 Relevant sections:")
    
    def search_nodes(nodes, depth=0):
        """Recursively search tree nodes for relevant information."""
        indent = "  " * depth
        for node in nodes:
            node_id = node.get('node_id', '')
            title = node.get('title', '')
            summary = node.get('summary', '')
            
            # Simple keyword matching (you could use LLM here)
            question_lower = question.lower()
            relevance_score = 0
            
            if any(word in title.lower() for word in question_lower.split()):
                relevance_score += 2
            if any(word in summary.lower() for word in question_lower.split()):
                relevance_score += 1
            
            if relevance_score > 0:
                print(f"{indent}├─ [{node_id}] {title}")
                print(f"{indent}│  📍 Pages {node.get('start_index')} - {node.get('end_index')}")
                print(f"{indent}│  📄 {summary[:150]}...")
                print()
            
            # Recurse into child nodes
            if 'nodes' in node and node['nodes']:
                search_nodes(node['nodes'], depth + 1)
    
    # Search top-level and nested nodes
    search_nodes([tree])
    if 'nodes' in tree:
        search_nodes(tree['nodes'])
    
    print("\n✨ Tip: For AI-powered answers, the full LLM query integration is coming soon!")
    print("   Currently using Claude Haiku 4.5 for document parsing.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python query-document.py <doc_id> \"<question>\"")
        print("\nExample:")
        print('  python query-document.py bca0f5fd-02d7-40dd-8ce4-3bbad4b22f8d "What is the revenue?"')
        sys.exit(1)
    
    doc_id = sys.argv[1]
    question = " ".join(sys.argv[2:])
    
    query_document(doc_id, question)
