import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Heart, Dumbbell, MessageSquare, Calendar, ChevronRight, Activity } from 'lucide-react';
import { boardApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import type { Post } from '@/types';

function PostCard({ post }: { post: Post }) {
  return (
    <Link
      to={`/board/${post.board_type}/${post.id}`}
      className="block p-4 rounded-lg hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
    >
      <h4 className="font-medium text-gray-900 line-clamp-1">{post.title}</h4>
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
    <div className="space-y-8">
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-primary-600 to-primary-800 rounded-2xl p-8 text-white overflow-hidden">
        <div className="relative z-10">
          <h1 className="text-3xl font-bold mb-3">건강한 삶, 함께 시작해요</h1>
          <p className="text-primary-100 mb-6 max-w-md">
            전문 의료 논문 기반 AI 건강 상담, 맞춤형 운동·식단 관리까지 한 곳에서.
          </p>
          {!isAuthenticated && (
            <div className="flex gap-3">
              <Link to="/register" className="bg-white text-primary-700 font-semibold px-5 py-2.5 rounded-lg hover:bg-primary-50 transition-colors">
                무료로 시작하기
              </Link>
              <Link to="/board/health" className="border border-white text-white px-5 py-2.5 rounded-lg hover:bg-white/10 transition-colors">
                건강정보 보기
              </Link>
            </div>
          )}
        </div>
        <Activity className="absolute right-8 top-1/2 -translate-y-1/2 w-32 h-32 text-primary-500 opacity-30" />
      </section>

      {/* Quick links */}
      <section className="grid grid-cols-2 gap-4">
        {isAuthenticated ? (
          <>
            {[
              { icon: Calendar, label: '운동 및 식단 기록', to: '/health',  color: 'text-green-500 bg-green-50' },
              { icon: MessageSquare, label: 'AI 상담',         to: '/chat',   color: 'text-purple-500 bg-purple-50' },
            ].map((item) => (
              <Link
                key={item.label}
                to={item.to}
                className="card flex flex-col items-center gap-3 py-6 hover:shadow-md transition-shadow text-center"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.color}`}>
                  <item.icon className="w-6 h-6" />
                </div>
                <span className="font-medium text-gray-700">{item.label}</span>
              </Link>
            ))}
          </>
        ) : (
          <>
            {[
              { icon: Heart,    label: '건강정보', to: '/board/health',    color: 'text-red-500 bg-red-50'   },
              { icon: Dumbbell, label: '운동정보', to: '/board/exercise',  color: 'text-blue-500 bg-blue-50' },
            ].map((item) => (
              <Link
                key={item.label}
                to={item.to}
                className="card flex flex-col items-center gap-3 py-6 hover:shadow-md transition-shadow text-center"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.color}`}>
                  <item.icon className="w-6 h-6" />
                </div>
                <span className="font-medium text-gray-700">{item.label}</span>
              </Link>
            ))}
          </>
        )}
      </section>

      {/* Latest posts */}
      <section className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-900 flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-500" /> 최신 건강정보
            </h2>
            <Link to="/board/health" className="text-sm text-primary-600 hover:underline flex items-center">
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
              <Dumbbell className="w-5 h-5 text-blue-500" /> 최신 운동정보
            </h2>
            <Link to="/board/exercise" className="text-sm text-primary-600 hover:underline flex items-center">
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
