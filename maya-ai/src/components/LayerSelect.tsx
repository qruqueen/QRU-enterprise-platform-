import { LAYERS, type Layer } from "../types";

interface LayerSelectProps {
  activeLayer: Layer;
  onSelect: (layer: Layer) => void;
}

export default function LayerSelect({ activeLayer, onSelect }: LayerSelectProps) {
  return (
    <nav className="layer-select" aria-label="Choose your learning layer">
      {LAYERS.map((layer) => {
        const active = layer.id === activeLayer;
        return (
          <button
            key={layer.id}
            type="button"
            className={`layer-tab${active ? " layer-tab--active" : ""}`}
            aria-pressed={active}
            onClick={() => onSelect(layer.id)}
          >
            <span className="layer-tab-name">{layer.name}</span>
            <span className="layer-tab-age">{layer.ageBand}</span>
          </button>
        );
      })}
    </nav>
  );
}
