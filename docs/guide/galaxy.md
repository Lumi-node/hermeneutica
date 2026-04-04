# Scripture Galaxy

The Scripture Galaxy is the flagship visualization — 31,102 KJV verses rendered as a 3D point cloud where **position = meaning**.

## How It Works

1. Each verse is embedded by Qwen3-Embedding-8B into a 2,000-dimensional vector
2. UMAP reduces these to 3D coordinates (preserving semantic neighborhoods)
3. The frontend renders all 31K points as GPU-instanced spheres in a single draw call

Verses that discuss similar topics cluster together, regardless of which book they come from.

## Controls

- **Orbit**: Click and drag to rotate
- **Zoom**: Scroll wheel
- **Hover**: Shows verse reference (e.g., "Gen 1:1")
- **Click**: Opens verse detail panel with text, interlinear, cross-references

## Color Encoding

Switch the "Color by" dropdown to change what colors represent:

| Mode | What It Shows |
|------|--------------|
| **Book** | Each of the 66 books gets a unique color (HSL rotation) |
| **Testament** | Amber = Old Testament, Blue = New Testament |
| **Genre** | 7 colors for Law, History, Wisdom, Prophecy, Gospel, Epistle, Apocalyptic |
| **Ethics** | Gradient based on max ethics relevance score (only classified chapters) |

## Size Encoding

| Mode | What It Shows |
|------|--------------|
| **Uniform** | All points the same size |
| **Cross-Refs** | Larger = more cross-references from that verse |
| **Ethics** | Larger = higher ethics relevance score |

## Cross-Reference Threads

The most visually stunning feature. Activate in the filter panel under "Cross-Reference Threads":

| Preset | Color | Connections |
|--------|-------|-------------|
| **OT Promises → NT** | Gold | 55,000 prophecy fulfillment arcs |
| **NT Quoting OT** | Sky blue | 39,000 NT-to-OT references |
| **Prophets → Gospels** | Orange | Messianic prophecies → Jesus' life |
| **Psalms → NT** | Purple | Psalms echoing through the early church |
| **Torah → NT** | Brown | Law reinterpreted in Christ |

These use additive blending — where many threads converge, the glow intensifies, revealing the densest connection zones.

## Filtering

- **Testament**: Show only OT or NT verses
- **Genre**: Check specific genres to isolate (e.g., only Prophecy books)
- **Books**: Select individual books

Filtered-out points are hidden (scale set to 0) without recreating the instanced mesh — so filtering is instant.
