import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { ArrowLeft, Plus, X } from 'lucide-react';
import { boardApi } from '@/services/api';
import toast from 'react-hot-toast';

export default function PostWritePage() {
  const { boardType } = useParams<{ boardType: string }>();
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: '', content: '' });
  const [tagInput, setTagInput] = useState('');
  const [tags, setTags] = useState<string[]>([]);

  const boardLabel = boardType === 'health' ? '건강정보' : boardType === 'exercise' ? '운동정보' : '자유게시판';

  const mutation = useMutation({
    mutationFn: () => boardApi.createPost({ ...form, board_type: boardType, tags }),
    onSuccess: (res) => {
      toast.success('게시글이 등록되었습니다.');
      navigate(`/board/${boardType}/${res.data.id}`);
    },
    onError: () => toast.error('게시글 등록에 실패했습니다.'),
  });

  const addTag = () => {
    const t = tagInput.trim().replace(/^#/, '');
    if (t && !tags.includes(t) && tags.length < 10) {
      setTags([...tags, t]);
      setTagInput('');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim() || !form.content.trim()) {
      toast.error('제목과 내용을 입력해 주세요.');
      return;
    }
    mutation.mutate();
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ArrowLeft className="w-4 h-4" /> 뒤로
      </button>

      <div className="card">
        <h1 className="text-xl font-bold text-gray-900 mb-6">{boardLabel} 글쓰기</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">제목</label>
            <input
              type="text"
              required
              maxLength={200}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="제목을 입력하세요"
              className="input-base"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">내용</label>
            <textarea
              required
              rows={15}
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
              placeholder="내용을 입력하세요"
              className="input-base resize-y"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">태그</label>
            <div className="flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                placeholder="태그 입력 후 Enter"
                className="input-base flex-1"
              />
              <button type="button" onClick={addTag} className="btn-secondary px-3">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {tags.map((t) => (
                  <span key={t} className="tag flex items-center gap-1">
                    #{t}
                    <button type="button" onClick={() => setTags(tags.filter((x) => x !== t))}>
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={() => navigate(-1)} className="btn-secondary flex-1">
              취소
            </button>
            <button type="submit" disabled={mutation.isPending} className="btn-primary flex-1">
              {mutation.isPending ? '등록 중...' : '등록하기'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
