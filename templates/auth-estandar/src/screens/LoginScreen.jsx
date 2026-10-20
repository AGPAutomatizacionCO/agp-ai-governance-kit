import { useRef, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import AgpLogo from "../components/AgpLogo";
import Icon from "../components/Icon";
import { appInfo } from "../config/msal";
import "../styles/login-estandar.css";

export default function LoginScreen() {
  const { login, loginError, loginLoading } = useAuth();
  const t = (texto) => texto;   // sin diccionario de idiomas: la pantalla va en español
  const nombreDesarrollo = appInfo.nombre || "Nombre del desarrollo";   // lo entrega la API (appName); la Mesa lo fija al desplegar
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let w = canvas.width = canvas.offsetWidth;
    let h = canvas.height = canvas.offsetHeight;
    const particles = Array.from({ length: 38 }, () => ({
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - .5) * .4, vy: (Math.random() - .5) * .4,
      r: Math.random() * 2.2 + .8, a: Math.random() * .55 + .18
    }));
    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(143,197,207,${p.a})`; ctx.fill();
      });
      particles.forEach((a, i) => particles.slice(i + 1).forEach(b => {
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 110) {
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(143,197,207,${.13 * (1 - d / 110)})`; ctx.stroke();
        }
      }));
      raf = requestAnimationFrame(draw);
    };
    draw();
    const onResize = () => {
      w = canvas.width = canvas.offsetWidth;
      h = canvas.height = canvas.offsetHeight;
    };
    window.addEventListener("resize", onResize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", onResize); };
  }, []);

  return (
    <div id="login-screen" className="screen active" style={{
      position: "relative", alignItems: "center", justifyContent: "center",
      minHeight: "100vh", height: "100vh", padding: "32px", overflow: "hidden",
      background: "radial-gradient(circle at 78% 22%, rgba(143,197,207,.22) 0, transparent 28%), radial-gradient(circle at 18% 82%, rgba(143,197,207,.12) 0, transparent 30%), linear-gradient(135deg,#06101d 0%,#071a2c 45%,#02070d 100%)",
      color: "#fff", display: "flex"
    }}>
      <canvas ref={canvasRef} id="glass-canvas" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none", zIndex: 0 }} />

      <div style={{ position: "absolute", top: "22px", right: "26px", zIndex: 2 }}>
      </div>

      <div id="login-shell" style={{ position: "relative", zIndex: 1, width: "100%", maxWidth: "1180px", display: "grid", gridTemplateColumns: "1.05fr .95fr", alignItems: "center", gap: "64px" }}>

        {/* Brand column */}
        <div id="login-brand" style={{ maxWidth: "500px", color: "#fff" }}>
          <div className="brand-icon" style={{ width: "88px", height: "88px", border: "1px solid rgba(143,197,207,.55)", borderRadius: "18px", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "24px", background: "rgba(143,197,207,.08)", boxShadow: "0 0 34px rgba(143,197,207,.28)" }}>
            <AgpLogo width={64} height={56} />
          </div>
          <h1 style={{ fontSize: "38px", lineHeight: 1.12, fontWeight: 800, letterSpacing: "-.8px", marginBottom: "16px" }}>
            {nombreDesarrollo}
          </h1>
          <p style={{ fontSize: "15px", color: "rgba(255,255,255,.78)", lineHeight: 1.7, marginBottom: "28px" }}>
            {t("AGP Colombia")}
          </p>
        </div>

        {/* Card column */}
        <div id="login-card" style={{ justifySelf: "end", width: "100%", maxWidth: "420px", borderRadius: "18px", background: "rgba(8,19,33,.72)", border: "1px solid rgba(148,210,255,.24)", boxShadow: "0 24px 70px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.08)", backdropFilter: "blur(16px)", overflow: "hidden" }}>
          <div style={{ padding: "30px 30px 12px" }}>
            <h1 style={{ color: "#fff", fontSize: "24px", fontWeight: 750, marginBottom: "8px", letterSpacing: "-.2px" }}>{t("Iniciar sesión")}</h1>
            <p style={{ color: "rgba(255,255,255,.66)", fontSize: "13px", lineHeight: 1.55 }}>{t("Accede con tu cuenta corporativa de Microsoft")}</p>
          </div>
          <div style={{ padding: "18px 30px 30px" }}>
            <p style={{ fontSize: "14px", color: "rgba(255,255,255,.76)", marginBottom: "24px", lineHeight: 1.7 }}>
              {t("Utiliza tu correo")} <strong style={{ color: "var(--brand)" }}>@agpglass.com</strong> {t("para acceder al sistema.")}
            </p>

            {loginError && (
              <div id="login-error" style={{ background: "rgba(220,83,83,.14)", border: "1px solid rgba(220,83,83,.55)", color: "#ffd7d7", borderRadius: "8px", padding: "10px 14px", marginBottom: "14px", fontSize: "13px" }}>
                {t(loginError)}
              </div>
            )}

            {loginLoading ? (
              <div id="login-loading" style={{ color: "rgba(255,255,255,.72)", textAlign: "center", padding: "14px", fontSize: "13px" }}>
                {t("Conectando con Microsoft…")}
              </div>
            ) : (
              <button
                id="ms-login-btn"
                onClick={login}
                style={{
                  width: "100%", background: "#fff", color: "#172033", border: "1px solid rgba(255,255,255,.9)",
                  borderRadius: "12px", padding: "14px 20px", boxShadow: "0 10px 26px rgba(0,0,0,.25)",
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                  gap: "10px", fontSize: "14px", fontWeight: 700, transition: "transform .15s, box-shadow .15s"
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--brand)"; e.currentTarget.style.transform = "translateY(-1px)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "rgba(255,255,255,.9)"; e.currentTarget.style.transform = "none"; }}
              >
                <svg width="20" height="20" viewBox="0 0 21 21"><rect x="1" y="1" width="9" height="9" fill="#f25022"/><rect x="11" y="1" width="9" height="9" fill="#7fba00"/><rect x="1" y="11" width="9" height="9" fill="#00a4ef"/><rect x="11" y="11" width="9" height="9" fill="#ffb900"/></svg>
                {t("Continuar con Microsoft")}
              </button>
            )}

            <p style={{ textAlign: "center", color: "rgba(255,255,255,.38)", fontSize: "11px", marginTop: "18px" }}>
              {t("Acceso exclusivo para empleados AGP Colombia")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
