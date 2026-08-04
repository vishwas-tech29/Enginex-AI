import { ChevronDown } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useRef } from 'react';

import { Button } from '@/components/common/Button';

const VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_065045_c44942da-53c6-4804-b734-f9e07fc22e08.mp4';

const NAV_ITEMS = [
  { label: 'Features', hasChevron: true },
  { label: 'Solutions', hasChevron: false },
  { label: 'Plans', hasChevron: false },
  { label: 'Learning', hasChevron: true },
];

// Real technologies this platform is actually built on — not fabricated
// customer/brand logos (the "Relied on by brands across the globe" framing
// this component started from would have been an unsubstantiated claim for
// a product with no customers yet).
const TECH_STACK = ['CadQuery', 'OpenCascade', 'Three.js', 'FastAPI', 'PostgreSQL', 'LangGraph'];
const MARQUEE_ITEMS = [...TECH_STACK, ...TECH_STACK];

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
    <div className="hero-theme relative min-h-screen overflow-hidden bg-[hsl(var(--hero-bg))] text-[hsl(var(--hero-fg))]">
      <video
        ref={videoRef}
        className="absolute inset-0 h-full w-full object-cover opacity-0"
        src={VIDEO_URL}
        muted
        autoPlay
        playsInline
        preload="auto"
      />

      <div className="relative z-10 flex min-h-screen flex-col overflow-visible">
        <div
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-1/2 h-[527px] w-[984px] -translate-x-1/2 -translate-y-1/2 bg-gray-950 opacity-90 blur-[82px]"
        />

        <header className="relative z-20">
          <nav className="flex items-center justify-between px-8 py-5">
            <div className="flex items-center gap-2">
              <div className="liquid-glass flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold">
                E
              </div>
              <span className="text-lg font-semibold tracking-wide" style={{ fontFamily: "'General Sans', sans-serif" }}>
                Enginex AI
              </span>
            </div>

            <div className="hidden items-center gap-8 md:flex">
              {NAV_ITEMS.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  className="flex items-center gap-1 text-sm font-medium text-[hsl(var(--hero-fg))]/90 transition-colors hover:text-[hsl(var(--hero-fg))]"
                >
                  {item.label}
                  {item.hasChevron && <ChevronDown size={14} />}
                </button>
              ))}
            </div>

            <Link href="/register">
              <Button variant="heroSecondary" className="px-4 py-2 text-sm">
                Sign Up
              </Button>
            </Link>
          </nav>
          <div className="mt-[3px] h-px bg-gradient-to-r from-transparent via-[hsl(var(--hero-fg))]/20 to-transparent" />
        </header>

        <main className="flex flex-1 flex-col items-center justify-center px-6 text-center">
          <h1
            className="text-[min(220px,16vw)] font-normal leading-[1.02] tracking-[-0.024em]"
            style={{ fontFamily: "'General Sans', sans-serif" }}
          >
            <span>Design </span>
            <span
              className="bg-clip-text text-transparent"
              style={{ backgroundImage: 'linear-gradient(to left, #6366f1, #a855f7, #fcd34d)' }}
            >
              AI
            </span>
          </h1>

          <p className="mt-[9px] max-w-md text-lg leading-8 text-[hsl(var(--hero-sub))] opacity-80">
            The most powerful AI copilot ever built
            <br />
            for real hardware engineering
          </p>

          <Link href="/register" className="mt-[25px]">
            <Button variant="heroSecondary" className="px-[29px] py-[24px] text-sm">
              Start building
            </Button>
          </Link>
        </main>

        <footer className="relative z-20 pb-10">
          <div className="mx-auto flex max-w-5xl flex-col items-center gap-12 px-6 md:flex-row md:items-center md:justify-between">
            <p className="whitespace-pre-line text-sm text-[hsl(var(--hero-fg))]/50">
              {'Built with modern,\nopen engineering tools'}
            </p>

            <div className="w-full overflow-hidden md:w-auto">
              <div className="flex w-max animate-hero-marquee gap-16">
                {MARQUEE_ITEMS.map((name, index) => (
                  <div key={`${name}-${index}`} className="flex shrink-0 items-center gap-3">
                    <div className="liquid-glass flex h-6 w-6 items-center justify-center rounded-lg text-xs font-semibold">
                      {name[0]}
                    </div>
                    <span className="text-base font-semibold text-[hsl(var(--hero-fg))]">{name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
