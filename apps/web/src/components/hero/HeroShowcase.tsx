import { ArrowRight, Globe, Instagram, Twitter } from 'lucide-react';
import { useEffect, useRef } from 'react';

export function HeroShowcase() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const fadingOutRef = useRef(false);
  const opacityRef = useRef(0);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const cancelCurrentAnimation = () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };

    const animateOpacity = (target: number, duration = 500) => {
      const startOpacity = opacityRef.current;
      const startTime = performance.now();

      cancelCurrentAnimation();

      const step = (now: number) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = progress < 0.5 ? 4 * progress * progress * progress : 1 - Math.pow(-2 * progress + 2, 3) / 2;
        const nextOpacity = startOpacity + (target - startOpacity) * eased;

        opacityRef.current = nextOpacity;
        video.style.opacity = nextOpacity.toFixed(3);

        if (progress < 1) {
          animationFrameRef.current = requestAnimationFrame(step);
        } else {
          animationFrameRef.current = null;
        }
      };

      animationFrameRef.current = requestAnimationFrame(step);
    };

    const fadeOut = () => {
      if (fadingOutRef.current) return;
      fadingOutRef.current = true;
      animateOpacity(0, 500);
    };

    const fadeIn = () => {
      fadingOutRef.current = false;
      animateOpacity(1, 500);
    };

    const handleLoadedData = () => {
      void video.play().catch(() => undefined);
      fadeIn();
    };

    const handleTimeUpdate = () => {
      if (!video.duration) return;
      const remaining = video.duration - video.currentTime;
      if (!fadingOutRef.current && remaining <= 0.55) {
        fadeOut();
      }
    };

    const handleEnded = () => {
      opacityRef.current = 0;
      video.style.opacity = '0';
      fadingOutRef.current = false;
      window.setTimeout(() => {
        video.currentTime = 0;
        void video.play().catch(() => undefined);
        fadeIn();
      }, 100);
    };

    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('ended', handleEnded);

    return () => {
      cancelCurrentAnimation();
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('ended', handleEnded);
    };
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-white">
      <video
        ref={videoRef}
        className="absolute inset-0 h-full w-full translate-y-[17%] object-cover"
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_115001_bcdaa3b4-03de-47e7-ad63-ae3e392c32d4.mp4"
        muted
        autoPlay
        playsInline
        preload="auto"
      />

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.15),transparent_45%),linear-gradient(180deg,rgba(0,0,0,0.58),rgba(0,0,0,0.84))]" />

      <div className="relative z-20 flex min-h-screen flex-col">
        <nav className="px-6 py-6 sm:px-8 lg:px-10">
          <div className="liquid-glass mx-auto flex max-w-5xl items-center justify-between rounded-full px-6 py-3">
            <div className="flex items-center gap-2">
              <div className="rounded-full bg-white/10 p-2">
                <Globe size={20} className="text-white" />
              </div>
              <span className="text-lg font-semibold tracking-wide text-white">Asme</span>
            </div>

            <div className="hidden items-center gap-8 md:flex">
              <a href="#features" className="text-sm font-medium text-white/80 transition-colors hover:text-white">
                Features
              </a>
              <a href="#pricing" className="text-sm font-medium text-white/80 transition-colors hover:text-white">
                Pricing
              </a>
              <a href="#about" className="text-sm font-medium text-white/80 transition-colors hover:text-white">
                About
              </a>
            </div>

            <div className="flex items-center gap-4">
              <button type="button" className="text-sm font-medium text-white transition-colors hover:text-white/80">
                Sign Up
              </button>
              <button type="button" className="liquid-glass rounded-full px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-white/5">
                Login
              </button>
            </div>
          </div>
        </nav>

        <main className="flex flex-1 flex-col items-center justify-center px-6 py-12 text-center sm:px-8 lg:px-10">
          <h1
            className="mb-8 whitespace-nowrap text-5xl tracking-tight text-white sm:text-6xl lg:text-7xl"
            style={{ fontFamily: "'Instrument Serif', serif" }}
          >
            Built for the curious
          </h1>

          <div className="w-full max-w-xl space-y-4">
            <form className="liquid-glass flex items-center gap-3 rounded-full py-2 pl-6 pr-2">
              <input
                type="email"
                placeholder="Enter your email"
                className="w-full bg-transparent text-base text-white outline-none placeholder:text-white/40"
                aria-label="Email"
              />
              <button type="submit" className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-black transition-transform hover:scale-105" aria-label="Submit">
                <ArrowRight size={20} />
              </button>
            </form>

            <p className="px-4 text-sm leading-relaxed text-white/85">
              Stay updated with the latest news and insights. Subscribe to our newsletter today and never miss out on exciting updates.
            </p>

            <div className="flex justify-center">
              <button type="button" className="liquid-glass rounded-full px-8 py-3 text-sm font-medium text-white transition-colors hover:bg-white/5">
                Read our manifesto
              </button>
            </div>
          </div>
        </main>

        <footer className="relative z-10 flex justify-center gap-4 pb-12">
          <a href="#instagram" aria-label="Instagram" className="liquid-glass rounded-full p-4 text-white/80 transition-all hover:bg-white/5 hover:text-white">
            <Instagram size={20} />
          </a>
          <a href="#twitter" aria-label="Twitter" className="liquid-glass rounded-full p-4 text-white/80 transition-all hover:bg-white/5 hover:text-white">
            <Twitter size={20} />
          </a>
          <a href="#globe" aria-label="Globe" className="liquid-glass rounded-full p-4 text-white/80 transition-all hover:bg-white/5 hover:text-white">
            <Globe size={20} />
          </a>
        </footer>
      </div>
    </div>
  );
}
