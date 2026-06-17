interface Props {
  className?: string;
}

export function LogoIcon({ className = "w-7 h-7" }: Props) {
  return (
    <img
      src="/favicon.svg"
      alt="MeraKia"
      className={className}
    />
  );
}
