import { Check } from "lucide-react";

export interface ColorOption {
  name: string;
  hex: string;
}

export const DEFAULT_COLOR_MAP: Record<string, string> = {
  branco: "#FFFFFF",
  white: "#FFFFFF",
  preto: "#1F2937",
  black: "#1F2937",
  vermelho: "#EF4444",
  red: "#EF4444",
  azul: "#3B82F6",
  blue: "#3B82F6",
  "azul marinho": "#1E3A8A",
  "azul royal": "#2563EB",
  "azul ceu": "#38BDF8",
  "azul claro": "#7DD3FC",
  verde: "#10B981",
  green: "#10B981",
  "verde militar": "#4B5320",
  "verde oliva": "#556B2F",
  "verde escuro": "#065F46",
  amarelo: "#FBBF24",
  yellow: "#FBBF24",
  "amarelo ouro": "#F59E0B",
  cinza: "#9CA3AF",
  gray: "#9CA3AF",
  grey: "#9CA3AF",
  "cinza chumbo": "#374151",
  rosa: "#EC4899",
  pink: "#EC4899",
  "rosa bebe": "#FBCFE8",
  roxo: "#8B5CF6",
  purple: "#8B5CF6",
  lilas: "#C084FC",
  laranja: "#F97316",
  orange: "#F97316",
  marrom: "#78350F",
  brown: "#78350F",
  bege: "#E2D9C8",
  dourado: "#D97706",
  gold: "#D97706",
  prateado: "#E2E8F0",
  silver: "#E2E8F0",
  vinho: "#7F1D1D",
  marsala: "#955251",
  terracota: "#E2725B",
};

export function isValidHex(hex: string): boolean {
  return /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/.test(hex);
}

export function expandHex(hex: string): string {
  if (hex.length === 4) {
    return `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}`.toUpperCase();
  }
  return hex.toUpperCase();
}

export function parseColorValue(val: unknown): ColorOption {
  if (typeof val === "object" && val !== null && "name" in val) {
    const item = val as { name: string; hex?: string };
    const hex =
      item.hex && isValidHex(item.hex)
        ? expandHex(item.hex)
        : DEFAULT_COLOR_MAP[item.name.toLowerCase().trim()] || "#3B82F6";
    return { name: item.name, hex };
  }

  const str = String(val).trim();

  // Verifica se a string contém código hexadecimal (ex: "Verde Militar (#4B5320)" ou "#4B5320")
  const hexMatch = str.match(/#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b/);
  if (hexMatch) {
    const rawHex = hexMatch[0];
    const hex = expandHex(rawHex);
    // Remove o hex e parênteses/dois pontos para deixar o nome comercial limpo
    let cleanName = str
      .replace(new RegExp(`\\(?${rawHex}\\)?`, "gi"), "")
      .replace(/[:\-–]/g, "")
      .trim();
    if (!cleanName) cleanName = hex;
    return { name: cleanName, hex };
  }

  // Busca no mapa de cores comuns
  const lower = str.toLowerCase();
  const hex = DEFAULT_COLOR_MAP[lower] || "#3B82F6";
  return { name: str, hex };
}

export function toPickerHex(hex?: string | null): string {
  if (!hex) return "#000000";
  let clean = hex.trim();
  if (!clean.startsWith("#")) clean = `#${clean}`;
  if (/^#[0-9A-Fa-f]{6}$/.test(clean)) {
    return clean.toLowerCase();
  }
  if (/^#[0-9A-Fa-f]{3}$/.test(clean)) {
    return `#${clean[1]}${clean[1]}${clean[2]}${clean[2]}${clean[3]}${clean[3]}`.toLowerCase();
  }
  return "#000000";
}

export function formatColorValue(name: string, hex: string): string {
  let cleanHex = hex.trim();
  if (cleanHex && !cleanHex.startsWith("#")) cleanHex = `#${cleanHex}`;
  cleanHex = cleanHex.toUpperCase();
  const cleanName = name.trim();

  if (cleanName && cleanHex && cleanName.toUpperCase() !== cleanHex) {
    return `${cleanName} (${cleanHex})`;
  }
  return cleanName || cleanHex || "#000000";
}

export function isColorOption(key: string, values: unknown): boolean {
  const lowerKey = key.toLowerCase();
  if (
    lowerKey.includes("cor") ||
    lowerKey.includes("color") ||
    lowerKey.includes("fundo") ||
    lowerKey.includes("background") ||
    lowerKey.includes("tonalidade") ||
    lowerKey.includes("paleta")
  ) {
    return true;
  }
  if (Array.isArray(values) && values.length > 0) {
    const first = values[0];
    if (typeof first === "object" && first !== null && "hex" in first) return true;
    if (typeof first === "string" && /#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b/.test(first)) return true;
  }
  return false;
}

export function normalizeColorOptions(values: unknown): ColorOption[] {
  if (!Array.isArray(values)) return [];
  return values.map(parseColorValue);
}

function isLightColor(hex: string): boolean {
  const cleanHex = hex.replace("#", "");
  if (cleanHex.length !== 6 && cleanHex.length !== 3) return true;
  const fullHex = cleanHex.length === 3
    ? `${cleanHex[0]}${cleanHex[0]}${cleanHex[1]}${cleanHex[1]}${cleanHex[2]}${cleanHex[2]}`
    : cleanHex;

  const r = parseInt(fullHex.substring(0, 2), 16);
  const g = parseInt(fullHex.substring(2, 4), 16);
  const b = parseInt(fullHex.substring(4, 6), 16);
  // Fórmula de luminância padrão
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6;
}

interface Props {
  colors: ColorOption[];
  selected?: string;
  onChange: (name: string) => void;
  required?: boolean;
}

export function ColorSwatchSelector({ colors, selected, onChange }: Props) {
  const selectedColor = colors.find(
    (c) =>
      selected === c.name ||
      selected === c.hex ||
      selected === `${c.name} (${c.hex})` ||
      selected === `${c.name} (${c.hex.toUpperCase()})` ||
      (selected ? selected.includes(c.hex) || (c.name && selected.includes(c.name)) : false)
  );

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2.5">
        {colors.map((color) => {
          const isSelected =
            selected === color.name ||
            selected === color.hex ||
            selected === `${color.name} (${color.hex})` ||
            selected === `${color.name} (${color.hex.toUpperCase()})` ||
            (selected ? selected.includes(color.hex) || (color.name && selected.includes(color.name)) : false);
          const isLight = isLightColor(color.hex);

          return (
            <button
              key={`${color.name}_${color.hex}`}
              type="button"
              onClick={() => {
                const formatted = formatColorValue(color.name, color.hex);
                onChange(formatted);
              }}
              title={`${color.name} (${color.hex})`}
              className={`group relative flex items-center justify-center w-9 h-9 rounded-xl transition-all duration-150 ${
                isSelected
                  ? "ring-2 ring-brand-500 ring-offset-2 dark:ring-offset-ink-900 scale-105 shadow-md"
                  : "hover:scale-105 hover:shadow-sm"
              } ${isLight ? "border border-slate-300 dark:border-ink-600" : "border border-transparent"}`}
              style={{ backgroundColor: color.hex }}
            >
              {isSelected && (
                <Check
                  className={`w-4 h-4 ${
                    isLight ? "text-slate-900 stroke-[3]" : "text-white stroke-[3]"
                  }`}
                />
              )}
              {/* Tooltip com Nome e Hex */}
              <span className="pointer-events-none absolute -bottom-7 left-1/2 -translate-x-1/2 px-2 py-0.5 text-[11px] font-medium bg-slate-900 text-white dark:bg-ink-700 rounded shadow opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                {color.name} <span className="font-mono text-[10px] opacity-80">{color.hex}</span>
              </span>
            </button>
          );
        })}
      </div>

      {selected && (
        <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2 pt-0.5">
          <span>Cor selecionada:</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">
            {selectedColor?.name || selected}
          </span>
          {selectedColor?.hex && (
            <span className="font-mono text-[11px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-ink-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-ink-600">
              {selectedColor.hex}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
