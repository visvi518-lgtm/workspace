import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Eye, EyeOff } from 'lucide-react';
import { authApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.login(form.email, form.password);
      const { access_token, user } = res.data;
      setAuth(user, access_token);
      toast.success(`${user.nickname}님, 환영합니다!`);
      navigate('/');
    } catch (err: any) {
      const msg = err.response?.data?.detail || '로그인에 실패했습니다.';
      if (msg.includes('dormant')) {
        toast.error('휴면 계정입니다. 이메일 인증 후 재활성화해 주세요.');
      } else if (msg.includes('banned')) {
        toast.error('정지된 계정입니다. 관리자에게 문의하세요.');
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center">
      <div className="w-full max-w-md">
        <div className="card">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mb-3">
              <Heart className="w-6 h-6 text-primary-600 fill-current" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">로그인</h1>
            <p className="text-sm text-gray-500 mt-1">건강한 삶을 함께 만들어요</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="example@email.com"
                className="input-base"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  required
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="비밀번호"
                  className="input-base pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
              {loading ? '로그인 중...' : '로그인'}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-500">
            계정이 없으신가요?{' '}
            <Link to="/register" className="text-primary-600 font-medium hover:underline">
              회원가입
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
