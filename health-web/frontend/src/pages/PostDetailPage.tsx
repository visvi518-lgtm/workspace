import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { ArrowLeft, ExternalLink, Trash2, Clock, Eye } from 'lucide-react';
import { boardApi, adminApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import CommentSection from '@/components/common/CommentSection';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import type { Post } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export default function PostDetailPage() {
  const { boardType, id } = useParams<{ boardType: string; id: string }>();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  const { data: post, isLoading } = useQuery<Post>({
    queryKey: ['post', id],
    queryFn: () => boardApi.getPost(Number(id)).then((r) => r.data),
    enabled: !!id,
  });

  const deleteMutation = useMutation({
    mutationFn: () => adminApi.deletePost(Number(id)),
    onSuccess: () => {
      toast.success('게시글이 삭제되었습니다.');
      navigate(`/board/${boardType}`);
    },
  });

  if (isLoading) return <LoadingSpinner />;
  if (!post) return <div className="text-center py-16 text-gray-400">게시글을 찾을 수 없습니다.</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <Link
        to={`/board/${boardType}`}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="w-4 h-4" /> 목록으로
      </Link>

      <div className="card">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900">{post.title}</h1>
          </div>
          {user?.is_admin && (
            <button
              onClick={() => deleteMutation.mutate()}
              className="text-red-500 hover:text-red-700 p-1"
              title="게시글 삭제"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-400 mb-6 pb-4 border-b border-gray-100">
          <span>{post.author.nickname}</span>
          <span className="flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {format(new Date(post.created_at), 'yyyy.MM.dd HH:mm')}
          </span>
          <span className="flex items-center gap-1">
            <Eye className="w-3.5 h-3.5" />{post.view_count}
          </span>
        </div>

        <div
          className="prose prose-sm max-w-none text-gray-700 leading-relaxed whitespace-pre-wrap"
          dangerouslySetInnerHTML={{ __html: post.content }}
        />

        {post.source_url && (
          <a
            href={post.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 mt-6 text-sm text-primary-600 hover:underline"
          >
            <ExternalLink className="w-4 h-4" /> 원문 보기
          </a>
        )}

        {post.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-gray-100">
            {post.tags.map((t) => <span key={t} className="tag">#{t}</span>)}
          </div>
        )}
      </div>

      <div className="card">
        <CommentSection postId={post.id} />
      </div>
    </div>
  );
}
