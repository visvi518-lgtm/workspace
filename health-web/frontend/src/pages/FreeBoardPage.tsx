import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { MessageSquare, Plus, Clock, Eye } from 'lucide-react';
import { boardApi } from '@/services/api';
import SearchBar from '@/components/common/SearchBar';
import Pagination from '@/components/common/Pagination';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import type { Post, PaginatedResponse } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';

export default function FreeBoardPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const navigate = useNavigate();

  const { data, isLoading } = useQuery<PaginatedResponse<Post>>({
    queryKey: ['posts', 'free', page, search],
    queryFn: () =>
      boardApi.getPosts({ board_type: 'free', page, per_page: 10, search }).then((r) => r.data),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-purple-500" />
          자유게시판
        </h1>
        <button
          onClick={() => navigate('/board/free/write')}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" /> 글쓰기
        </button>
      </div>

      <SearchBar onSearch={(q) => { setSearch(q); setPage(1); }} placeholder="제목, 내용으로 검색" />

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
                to={`/board/free/${post.id}`}
                className="flex items-center gap-4 py-4 px-2 hover:bg-gray-50 rounded-lg transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900 line-clamp-1 group-hover:text-primary-600">
                    {post.title}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-gray-400 mt-1">
                    <span>{post.author.nickname}</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: ko })}
                    </span>
                    <span className="flex items-center gap-1"><Eye className="w-3 h-3" />{post.view_count}</span>
                    <span className="flex items-center gap-1"><MessageSquare className="w-3 h-3" />{post.comment_count}</span>
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      )}

      <Pagination page={page} totalPages={data?.total_pages ?? 1} onPageChange={setPage} />
    </div>
  );
}
