import React from "react";

function Logo() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ marginRight: "12px" }}
    >
      {/* Background gradient box */}
      <rect width="32" height="32" rx="6" fill="url(#gradient)" />

      {/* Document icon - represents invoice */}
      <path
        d="M8 4C7.44772 4 7 4.44772 7 5V27C7 27.5523 7.44772 28 8 28H24C24.5523 28 25 27.5523 25 27V9L19 3H8Z"
        fill="white"
        opacity="0.95"
      />

      {/* Document lines - data extraction */}
      <line x1="10" y1="12" x2="22" y2="12" stroke="url(#gradient)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="10" y1="16" x2="22" y2="16" stroke="url(#gradient)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="10" y1="20" x2="18" y2="20" stroke="url(#gradient)" strokeWidth="1.5" strokeLinecap="round" />

      {/* Gradient definition */}
      <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F4AD0B" />
          <stop offset="50%" stopColor="#FC7900" />
          <stop offset="100%" stopColor="#E3434A" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default Logo;
