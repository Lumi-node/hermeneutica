# Exploration Tools

The bottom toolbar provides three deep-dive tools accessible from any 3D view.

## Theme Tracer

**Type a biblical theme and trace it from Genesis to Revelation.**

1. Type a theme name (autocomplete suggests as you type)
2. See a timeline bar chart showing verse density per book
3. Scroll through every verse tagged with that theme, ordered chronologically

**Quick picks:** Love, Faith, Justice, Mercy, Covenant, Prayer

The bar chart uses amber for OT books and blue for NT books, with bar height proportional to verse count. This reveals how themes develop across scripture — some concentrate in a few books, others thread through the entire Bible.

## Shortest Path

**Find how any two nodes connect through the knowledge graph.**

Enter two node IDs (verse, theme, or Strong's word) and the tool finds the shortest path between them using BFS through the 549K-edge graph.

Each hop in the path shows:

- The node (verse text, theme name, or word definition)
- The connection type (cross-reference, shared topic, semantic similarity, word family)
- The edge weight (connection strength)

**Try:** Verse 1 (Genesis 1:1) → Verse 21242 (John 1:1) — discover the chain of connections between "In the beginning" passages.

## Principle Search

**Search AI-extracted moral principles using natural language.**

The system has 1,124 distilled moral principles extracted from 288 classified chapters. Search with plain language:

- "What does the Bible teach about forgiveness?"
- "anger"
- "generosity"
- "justice for the poor"

Each result shows:

- The principle text (in modern, actionable language)
- Source chapter and book
- Genre classification
- Theme tags
- Teaching type (direct command, implicit principle, by example, metaphor)
- Ethics score breakdown (expandable bar chart across 5 dimensions)
