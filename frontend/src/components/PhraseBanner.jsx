import '../styles/banner.css';

const phrases = [
  "El Balance es la clave del éxito.",
  "Cada día es una nueva oportunidad para organizarte.",
  "Planifica tu semana, conquista tus metas.",
  "Organiza hoy, disfruta mañana.",
  "Una semana ordenada, una mente despejada."
];

export default function PhraseBanner() {
  const phrase = phrases[Math.floor(Math.random() * phrases.length)];
  return <div className="banner">{phrase}</div>;
}
