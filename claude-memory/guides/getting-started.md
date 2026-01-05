---
title: Getting Started with bloxcue
category: guides
tags: [bloxcue, tutorial, getting-started]
---

# Getting Started with bloxcue

Welcome! This is your first context block. Here's how to use bloxcue:

## Creating Blocks

Each block is a markdown file with:

1. **Frontmatter** (the YAML at the top)
   - `title`: What this block is about
   - `category`: Folder it belongs to
   - `tags`: Keywords for better search

2. **Content** (everything after the frontmatter)
   - Keep it focused on one topic
   - Use headers to organize
   - Include code snippets, commands, links

## Example Block

```markdown
---
title: My API Reference
category: apis
tags: [api, rest, authentication]
---

# My API Reference

Base URL: https://api.example.com

## Authentication
Use Bearer token in headers...
```

## Tips

- **One topic per file** - Better search precision
- **Descriptive tags** - `[deployment, aws, production]` not just `[deploy]`
- **Re-index after adding** - Run the indexer to update search

## Commands

```bash
# Index all blocks
python3 ~/.claude-memory/scripts/indexer.py

# Search blocks
python3 ~/.claude-memory/scripts/indexer.py --search "keyword"

# List all blocks
python3 ~/.claude-memory/scripts/indexer.py --list
```

## Next Steps

1. Delete this file (or keep it as reference)
2. Create your first real block
3. Ask Claude about a topic you documented

Claude will automatically retrieve relevant blocks!
