# Knowledge Graph

The Knowledge Graph explorer lets you navigate the 549,440 connections between verses, themes, and words.

## How It Works

Select a starting node (verse, theme, or word) and the graph loads its **neighborhood** — all nodes connected within N hops. A force-directed layout arranges them in 3D, where connected nodes pull together and unconnected nodes repel.

## Node Types

| Type | Shape | Color | Count |
|------|-------|-------|-------|
| **Verse** | Sphere | Blue | 31,102 |
| **Theme** | Large sphere | Green | 4,980 |
| **Strong's Word** | Sphere | Gold | 14,298 |

## Edge Types

| Type | Color | Count | Meaning |
|------|-------|-------|---------|
| **cross_ref** | Blue | 432,944 | Scholarly cross-reference (Treasury of Scripture Knowledge) |
| **twot_family** | Gold | 7,347 | Hebrew words sharing the same root (TWOT) |
| **nave_topic** | Green | 85,128 | Verse tagged with a Nave's Topical Bible theme |
| **semantic_sim** | Red | 15,597 | AI embeddings show >85% cosine similarity |
| **strongs_sim** | Pink | 8,424 | Strong's definitions are semantically similar |

## Controls

- **Hops** (1/2/3): How many levels of connections to load
    - 1 hop: Direct connections only (star pattern from center)
    - 2 hops: Connections between connected nodes (web starts forming)
    - 3 hops: Rich network structure (friends-of-friends-of-friends)
- **Edge Types**: Toggle which relationship types to show
- **Min Weight**: Filter out weak connections (higher = only strongest links)
- **Click a node**: Re-centers the graph on that node

## The Info Panel

The bottom-right panel shows:

- What node you're exploring
- Network stats (node/edge counts)
- Connection type breakdown with colors
- Hover detail showing a node's connections and their types

## Default Entry Point

When you first switch to the Knowledge Graph, it loads the neighborhood of the **"Love"** theme — a well-connected central concept with ties across both testaments.
