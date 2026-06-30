import { Link } from 'react-router-dom';
import BannerCarousel from '@/components/common/BannerCarousel';
import { useQuery } from '@tanstack/react-query';
import {
  Heart, Dumbbell, MessageSquare, CalendarDays,
  ChevronRight, Activity, Brain, Shield,
} from 'lucide-react';
import { boardApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import type { Post } from '@/types';

function PostCard({ post }: { post: Post }) {
  return (
    <Link
      to={`/board/${post.board_type}/${post.id}`}
      className="block p-4 rounded-lg hover:bg-primary-50 transition-colors border-b border-gray-100 last:border-0 group"
    >
      <h4 className="font-medium text-gray-900 line-clamp-1 group-hover:text-primary-700 transition-colors">{post.title}</h4>
      {post.summary && (
        <p className="text-sm text-gray-500 mt-1 line-clamp-2">{post.summary}</p>
      )}
      <div className="flex items-center gap-2 mt-2">
        {post.tags.slice(0, 3).map((t) => (
          <span key={t} className="tag">{t}</span>
        ))}
        <span className="ml-auto text-xs text-gray-400">
          {formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: ko })}
        </span>
      </div>
    </Link>
  );
}

export default function HomePage() {
  const { isAuthenticated } = useAuthStore();

  const { data: healthPosts } = useQuery({
    queryKey: ['posts', 'health', 'home'],
    queryFn: () => boardApi.getPosts({ board_type: 'health', per_page: 5 }).then((r) => r.data.items as Post[]),
  });

  const { data: exercisePosts } = useQuery({
    queryKey: ['posts', 'exercise', 'home'],
    queryFn: () => boardApi.getPosts({ board_type: 'exercise', per_page: 5 }).then((r) => r.data.items as Post[]),
  });

  return (
    <div className="space-y-10">

      {/* ── 배너 캐러셀 (관리자 설정, 없으면 숨김) ── */}
      <BannerCarousel />

      {/* ── Hero ── */}
      <section className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-primary-700 via-primary-600 to-secondary-500 p-10 text-white">
        {/* 배경 장식 */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-16 -right-16 w-72 h-72 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-16 -left-16 w-72 h-72 bg-secondary-400/20 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-3 py-1.5 rounded-full text-sm font-medium mb-5">
            <Activity className="w-4 h-4" /> AI 기반 건강 관리 플랫폼
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold leading-tight mb-4">
            건강한 삶,<br />
            <span className="text-primary-200">MOTI</span>와 함께
          </h1>
          <p className="text-primary-100 text-lg mb-8 leading-relaxed">
            전문 의료 논문 기반 AI 건강 상담과<br className="hidden sm:block" />
            맞춤형 운동·식단 관리를 한 곳에서 경험하세요.
          </p>
          {!isAuthenticated ? (
            <div className="flex flex-wrap gap-3">
              <Link
                to="/register"
                className="bg-white text-primary-700 font-bold px-6 py-3 rounded-xl hover:bg-primary-50 transition-colors shadow-lg"
              >
                무료로 시작하기
              </Link>
              <Link
                to="/board/health"
                className="border-2 border-white/60 text-white px-6 py-3 rounded-xl hover:bg-white/10 transition-colors"
              >
                건강정보 둘러보기
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap gap-3">
              <Link
                to="/health"
                className="bg-white text-primary-700 font-bold px-6 py-3 rounded-xl hover:bg-primary-50 transition-colors shadow-lg"
              >
                기록 시작하기
              </Link>
              <Link
                to="/chat"
                className="border-2 border-white/60 text-white px-6 py-3 rounded-xl hover:bg-white/10 transition-colors"
              >
                AI 상담하기
              </Link>
            </div>
          )}
        </div>

        {/* 오른쪽 장식 아이콘 */}
        <div className="absolute right-10 bottom-8 hidden lg:flex flex-col gap-4 opacity-40">
          <Heart className="w-10 h-10 text-white" />
          <Brain className="w-10 h-10 text-white" />
          <Shield className="w-10 h-10 text-white" />
        </div>
      </section>

      {/* ── 특징 카드 ── */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { icon: Brain,       color: 'bg-primary-100 text-primary-600',   title: 'AI 건강 상담',    desc: '의료 논문 기반 정확한 건강 정보' },
          { icon: Activity,    color: 'bg-secondary-100 text-secondary-600', title: '맞춤 운동 관리',   desc: '운동 목적에 맞는 일지 & 기록' },
          { icon: CalendarDays, color: 'bg-purple-100 text-purple-600',     title: '식단 트래킹',      desc: 'AI 칼로리 분석으로 손쉬운 관리' },
        ].map((f) => (
          <div key={f.title} className="card flex items-start gap-4 hover:shadow-md transition-shadow">
            <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${f.color}`}>
              <f.icon className="w-5 h-5" />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{f.title}</p>
              <p className="text-sm text-gray-500 mt-0.5">{f.desc}</p>
            </div>
          </div>
        ))}
      </section>

      {/* ── 퀵 링크 ── */}
      <section>
        <h2 className="text-lg font-bold text-gray-900 mb-4">바로가기</h2>
        <div className="grid grid-cols-2 gap-4">
          {isAuthenticated ? (
            <>
              {[
                { icon: CalendarDays, label: '운동 및 식단 기록', to: '/health',        color: 'bg-primary-500',   light: 'bg-primary-50 text-primary-600'   },
                { icon: MessageSquare, label: 'AI 상담',          to: '/chat',           color: 'bg-purple-500',    light: 'bg-purple-50 text-purple-600'     },
                { icon: Heart,         label: '건강정보',          to: '/board/health',   color: 'bg-rose-500',      light: 'bg-rose-50 text-rose-600'         },
                { icon: Dumbbell,      label: '운동정보',          to: '/board/exercise', color: 'bg-secondary-500', light: 'bg-secondary-50 text-secondary-600' },
              ].map((item) => (
                <Link
                  key={item.label}
                  to={item.to}
                  className="card flex items-center gap-3 py-4 px-5 hover:shadow-md transition-all hover:-translate-y-0.5 group"
                >
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${item.light}`}>
                    <item.icon className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-gray-700 group-hover:text-primary-700 transition-colors">{item.label}</span>
                  <ChevronRight className="w-4 h-4 text-gray-300 ml-auto group-hover:text-primary-400 transition-colors" />
                </Link>
              ))}
            </>
          ) : (
            <>
              {[
                { icon: Heart,    label: '건강정보', to: '/board/health',   light: 'bg-rose-50 text-rose-600'         },
                { icon: Dumbbell, label: '운동정보', to: '/board/exercise', light: 'bg-secondary-50 text-secondary-600' },
              ].map((item) => (
                <Link
                  key={item.label}
                  to={item.to}
                  className="card flex flex-col items-center gap-3 py-8 hover:shadow-md transition-all hover:-translate-y-0.5 text-center group"
                >
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${item.light}`}>
                    <item.icon className="w-7 h-7" />
                  </div>
                  <span className="font-semibold text-gray-700 group-hover:text-primary-700 transition-colors">{item.label}</span>
                </Link>
              ))}
            </>
          )}
        </div>
      </section>

      {/* ── 최신 게시글 ── */}
      <section className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              <div className="w-7 h-7 bg-rose-100 rounded-lg flex items-center justify-center">
                <Heart className="w-4 h-4 text-rose-500" />
              </div>
              최신 건강정보
            </h2>
            <Link to="/board/health" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-0.5 font-medium">
              더보기 <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div>
            {(healthPosts ?? []).map((p) => <PostCard key={p.id} post={p} />)}
            {!healthPosts?.length && <p className="text-sm text-gray-400 text-center py-8">등록된 글이 없습니다.</p>}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              <div className="w-7 h-7 bg-secondary-100 rounded-lg flex items-center justify-center">
                <Dumbbell className="w-4 h-4 text-secondary-600" />
              </div>
              최신 운동정보
            </h2>
            <Link to="/board/exercise" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-0.5 font-medium">
              더보기 <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <div>
            {(exercisePosts ?? []).map((p) => <PostCard key={p.id} post={p} />)}
            {!exercisePosts?.length && <p className="text-sm text-gray-400 text-center py-8">등록된 글이 없습니다.</p>}
          </div>
        </div>
      </section>
    </div>
  );
}
