import { useState, useEffect, useRef } from "react";

interface Country {
  code: string;
  name: string;
  dialCode: string;
  mask: string;
}

const countries: Country[] = [
  { code: "BR", name: "Brasil", dialCode: "55", mask: "(XX) XXXXX-XXXX" },
  { code: "US", name: "Estados Unidos", dialCode: "1", mask: "(XXX) XXX-XXXX" },
  { code: "AR", name: "Argentina", dialCode: "54", mask: "(XXX) XXX-XXXX" },
  { code: "CL", name: "Chile", dialCode: "56", mask: "(X) XXXX-XXXX" },
  { code: "CO", name: "Colômbia", dialCode: "57", mask: "(XXX) XXX-XXXX" },
  { code: "PE", name: "Peru", dialCode: "51", mask: "(XXX) XXX-XXXX" },
  { code: "MX", name: "México", dialCode: "52", mask: "(XXX) XXX-XXXX" },
  { code: "ES", name: "Espanha", dialCode: "34", mask: "(XXX) XXX-XXXX" },
  { code: "PT", name: "Portugal", dialCode: "351", mask: "(XXX) XXX-XXXX" },
  { code: "FR", name: "França", dialCode: "33", mask: "(X) XX XX XX XX" },
  { code: "DE", name: "Alemanha", dialCode: "49", mask: "(XXXX) XXXXXXX" },
  { code: "IT", name: "Itália", dialCode: "39", mask: "(XXX) XXXXXXX" },
  { code: "GB", name: "Reino Unido", dialCode: "44", mask: "(XXXX) XXXXXX" },
];

interface PhoneInputProps {
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  className?: string;
}

export function PhoneInput({ value, onChange, required = false, className = "" }: PhoneInputProps) {
  const [selectedCountry, setSelectedCountry] = useState<Country>(countries[0]);
  const [phoneNumber, setPhoneNumber] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Parse existing value to set country and phone number reactively
  useEffect(() => {
    if (!value) {
      setPhoneNumber("");
      return;
    }

    const clean = value.replace(/\D/g, "");
    if (!clean) {
      setPhoneNumber("");
      return;
    }

    // 1) Se veio com prefixo +, ex: +55 62999998888
    let foundCountry = countries.find((c) => value.trim().startsWith(`+${c.dialCode}`));
    let numberWithoutDial = "";

    if (foundCountry) {
      numberWithoutDial = clean.slice(foundCountry.dialCode.length);
    } else {
      // 2) Se veio apenas números (ex: 5562999998888 salvo no banco)
      foundCountry = countries.find(
        (c) => clean.startsWith(c.dialCode) && clean.length > c.dialCode.length + 7
      );
      if (foundCountry) {
        numberWithoutDial = clean.slice(foundCountry.dialCode.length);
      } else {
        // 3) Padrão Brasil (DDD + número)
        foundCountry = countries[0];
        numberWithoutDial = clean;
      }
    }

    setSelectedCountry(foundCountry);
    const formatted = formatPhone(numberWithoutDial, foundCountry.mask);
    setPhoneNumber(formatted);
  }, [value]);


  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const formatPhone = (value: string, mask: string): string => {
    const numbers = value.replace(/\D/g, "");
    let formatted = "";
    let numberIndex = 0;

    for (let i = 0; i < mask.length && numberIndex < numbers.length; i++) {
      if (mask[i] === "X") {
        formatted += numbers[numberIndex];
        numberIndex++;
      } else {
        formatted += mask[i];
      }
    }

    return formatted;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const formatted = formatPhone(e.target.value, selectedCountry.mask);
    setPhoneNumber(formatted);
    const fullValue = `+${selectedCountry.dialCode} ${formatted.replace(/\D/g, "")}`;
    onChange(fullValue);
  };

  const handleCountryChange = (country: Country) => {
    setSelectedCountry(country);
    setIsOpen(false);
    // Reformat phone number with new country's mask
    const numbers = phoneNumber.replace(/\D/g, "");
    const newFormatted = formatPhone(numbers, country.mask);
    setPhoneNumber(newFormatted);
    const fullValue = `+${country.dialCode} ${numbers}`;
    onChange(fullValue);
  };

  const getFlagUrl = (code: string) => {
    return `https://flagcdn.com/w20/${code.toLowerCase()}.png`;
  };

  return (
    <div className={`flex gap-2 ${className}`}>
      <div className="relative" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-ink-700 min-w-[100px] focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <img
            src={getFlagUrl(selectedCountry.code)}
            alt={selectedCountry.name}
            className="w-5 h-auto object-cover"
          />
          <span className="text-sm font-medium">+{selectedCountry.dialCode}</span>
          <span className="text-slate-400">▼</span>
        </button>

        {isOpen && (
          <div className="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-ink-800 border border-slate-300 dark:border-slate-600 rounded-lg shadow-lg z-50 max-h-60 overflow-auto">
            {countries.map((country) => (
              <button
                key={country.code}
                type="button"
                onClick={() => handleCountryChange(country)}
                className="w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-100 dark:hover:bg-ink-700 text-left"
              >
                <img
                  src={getFlagUrl(country.code)}
                  alt={country.name}
                  className="w-5 h-auto object-cover"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium">{country.name}</div>
                  <div className="text-xs text-slate-500">+{country.dialCode}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <input
        type="text"
        value={phoneNumber}
        onChange={handlePhoneChange}
        placeholder={selectedCountry.mask}
        required={required}
        className="flex-1 input"
      />
    </div>
  );
}
