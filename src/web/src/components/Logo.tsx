import { Link } from "react-router-dom";
import { LogoIcon } from "./LogoIcon";

interface Props {
  size?: "sm" | "md" | "lg";
  asLink?: boolean;
}

export function Logo({ size = "md", asLink = true }: Props) {
  const sizes = {
    sm: { icon: "w-6 h-6", text: "text-lg" },
    md: { icon: "w-8 h-8", text: "text-xl" },
    lg: { icon: "w-12 h-12", text: "text-3xl" },
  };
  const s = sizes[size];

  const inner = (
    <div className="flex items-center gap-2">
      <LogoIcon className={s.icon} />
      <span className={`${s.text} font-extrabold tracking-tight`}>
        <span className="text-slate-900 dark:text-white">MeraK</span>
        <span className="text-accent-500">ia</span>
      </span>
    </div>
  );

  return asLink ? <Link to="/">{inner}</Link> : inner;
}
