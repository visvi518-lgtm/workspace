import { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { bannerApi } from '@/services/api';

interface BannerMeta {
  id: number;
  title?: string;
  subtitle?: string;
  link_url?: string;
  has_image: boolean;
}

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1';

export default function BannerCarousel() {
  const { data: banners = [] } = useQuery<BannerMeta[]>({
    queryKey: ['banners'],
    queryFn: () => bannerApi.getBanners().then((r) => r.data),
  });

  const total = banners.length;
  const [current, setCurrent] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval>>();

  useEffect(() => {
    if (total <= 1) return;
    timerRef.current = setInterval(
      () => setCurrent((c) => (c + 1) % total),
      5000
    );
    return () => clearInterval(timerRef.current);
  }, [total]);

  if (total === 0) return null;

  const goTo = (idx: number) => {
    clearInterval(timerRef.current);
    setCurrent(idx);
  };

  return (
    <section className="relative rounded-3xl overflow-hidden bg-gray-800 h-48 sm:h-64">
      {/* Slide track */}
      <div
        className="flex h-full transition-transform duration-500 ease-in-out"
        style={{
          width: `${total * 100}%`,
          transform: `translateX(-${current * (100 / total)}%)`,
        }}
      >
        {banners.map((banner) => {
          const inner = (
            <>
              {banner.has_image ? (
                <img
                  src={`${API_BASE}/banners/${banner.id}/image`}
                  alt={banner.title ?? '배너'}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-br from-primary-700 to-primary-500" />
              )}

              {(banner.title || banner.subtitle) && (
                <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/20 to-transparent flex items-center px-8 sm:px-12">
                  <div className="text-white max-w-lg">
                    {banner.title && (
                      <h2 className="text-xl sm:text-3xl font-bold leading-tight mb-1.5">
                        {banner.title}
                      </h2>
                    )}
                    {banner.subtitle && (
                      <p className="text-sm sm:text-base text-white/80 leading-relaxed">
                        {banner.subtitle}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </>
          );

          return banner.link_url ? (
            <a
              key={banner.id}
              href={banner.link_url}
              target="_blank"
              rel="noopener noreferrer"
              className="h-full relative flex-shrink-0 block"
              style={{ width: `${100 / total}%` }}
            >
              {inner}
            </a>
          ) : (
            <div
              key={banner.id}
              className="h-full relative flex-shrink-0"
              style={{ width: `${100 / total}%` }}
            >
              {inner}
            </div>
          );
        })}
      </div>

      {/* Dot navigation */}
      {total > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
          {banners.map((_, i) => (
            <button
              key={i}
              onClick={() => goTo(i)}
              aria-label={`배너 ${i + 1}`}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === current
                  ? 'w-6 bg-white'
                  : 'w-1.5 bg-white/50 hover:bg-white/75'
              }`}
            />
          ))}
        </div>
      )}
    </section>
  );
}
