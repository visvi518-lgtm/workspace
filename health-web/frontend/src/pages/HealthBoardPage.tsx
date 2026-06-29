import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Heart, Dumbbell, Plus, Clock, Eye } from 'lucide-react';
import { boardApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import SearchBar from '@/components/common/SearchBar';
import Pagination from '@/components/common/Pagination';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import type { Post, PaginatedResponse } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

const POPULAR_TAGS: Record<string, string[]> = {
  health: ['혈압', '당뇨', '수면', '면역력', '비타민', '스트레스'],
  exercise: ['스트레칭', '유산소', '근력', '자세교정', '홈트', 'PT'],
};

export default function HealthBoardPage() {
  const { boardType = 'health' } = useParams<{ boardType: string }>();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [tag, setTag] = useState('');
  const { isAuthenticated } = useAuthStore();

  const isHealth = boardType === 'health';
  const title = isHealth ? '건강정보' : '운동정보';
  const Icon = isHealth ? Heart : Dumbbell;

  const { data, isLoading } = useQuery<PaginatedResponse<Post>>({
    queryKey: ['posts', boardType, page, search, tag],
    queryFn: () =>
      boardApi.getPosts({ board_type: boardType, page, per_page: 10, search, tag })
        .then((r) => r.data),
  });

  const handleSearch = (q: string) => {
    setSearch(q);
    setTag('');
    setPage(1);
  };

  const handleTagClick = (t: string) => {
    setTag(t);
    setSearch('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Icon className={`w-6 h-6 ${isHealth ? 'text-red-500' : 'text-blue-500'}`} />
          {title}
        </h1>
      </div>

      {/* Search */}
      <SearchBar
        onSearch={handleSearch}
        placeholder={`${title} 검색`}
        tags={POPULAR_TAGS[boardType] ?? []}
        onTagClick={handleTagClick}
      />
      {tag && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">필터:</span>
          <span className="tag">#{tag}</span>
          <button onClick={() => setTag('')} className="text-xs text-gray-400 hover:text-gray-600">✕ 초기화</button>
        </div>
      )}

      {/* Post list */}
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="card divide-y divide-gray-100">
          {(data?.items ?? []).length === 0 ? (
            <p className="text-center text-gray-400 py-12">게시글이 없습니다.</p>
          ) : (
            data?.items.map((post) => (
              <Link
                key={post.id}
                to={`/board/${boardType}/${post.id}`}
                className="flex gap-4 py-4 px-2 hover:bg-gray-50 rounded-lg transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-gray-900 line-clamp-1 group-hover:text-primary-600 transition-colors">
                      {post.title}
                    </h3>
                  </div>
                  {post.summary && (
                    <p className="text-sm text-gray-500 line-clamp-2 mb-2">{post.summary}</p>
                  )}
                  <div className="flex items-center gap-3 text-xs text-gray-400 flex-wrap">
                    <span>{post.author.nickname}</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: ko })}
                    </span>
                    <span className="flex items-center gap-1">
                      <Eye className="w-3 h-3" />{post.view_count}
                    </span>
                    {post.tags.slice(0, 3).map((t) => (
                      <span key={t} className="tag text-xs" onClick={(e) => { e.preventDefault(); handleTagClick(t); }}>#{t}</span>
                    ))}
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      )}

      <Pagination
        page={page}
        totalPages={data?.total_pages ?? 1}
        onPageChange={setPage}
      />
    </div>
  );
}
