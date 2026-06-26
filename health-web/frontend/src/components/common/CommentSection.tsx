import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MessageCircle, Trash2 } from 'lucide-react';
import { boardApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { Comment } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import toast from 'react-hot-toast';

interface Props {
  postId: number;
}

export default function CommentSection({ postId }: Props) {
  const [content, setContent] = useState('');
  const { isAuthenticated, user } = useAuthStore();
  const queryClient = useQueryClient();

  const { data: comments = [] } = useQuery<Comment[]>({
    queryKey: ['comments', postId],
    queryFn: () => boardApi.getComments(postId).then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => boardApi.createComment(postId, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
      setContent('');
      toast.success('댓글이 등록되었습니다.');
    },
    onError: () => toast.error('댓글 등록에 실패했습니다.'),
  });

  const deleteMutation = useMutation({
    mutationFn: (commentId: number) => boardApi.deleteComment(postId, commentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', postId] });
      toast.success('댓글이 삭제되었습니다.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    createMutation.mutate();
  };

  return (
    <div className="space-y-4">
      <h3 className="flex items-center gap-2 font-semibold text-gray-900">
        <MessageCircle className="w-5 h-5 text-primary-600" />
        댓글 {comments.length}개
      </h3>

      {isAuthenticated && (
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="댓글을 입력하세요"
            className="input-base flex-1"
            maxLength={500}
          />
          <button
            type="submit"
            disabled={createMutation.isPending || !content.trim()}
            className="btn-primary whitespace-nowrap"
          >
            등록
          </button>
        </form>
      )}

      <div className="space-y-3">
        {comments.map((comment) => (
          <div key={comment.id} className="flex gap-3 p-3 rounded-lg bg-gray-50">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-medium text-sm text-gray-900">{comment.author.nickname}</span>
                <span className="text-xs text-gray-400">
                  {formatDistanceToNow(new Date(comment.created_at), { addSuffix: true, locale: ko })}
                </span>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed">{comment.content}</p>
            </div>
            {(user?.id === comment.author.id || user?.is_admin) && (
              <button
                onClick={() => deleteMutation.mutate(comment.id)}
                className="text-gray-400 hover:text-red-500 transition-colors p-1"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        {comments.length === 0 && (
          <p className="text-center text-gray-400 py-6 text-sm">첫 댓글을 남겨보세요!</p>
        )}
      </div>
    </div>
  );
}
