import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Eye, EyeOff } from 'lucide-react';
import { authApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

const BACKEND = import.meta.env.VITE_API_URL ?? '';

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

          {/* Social login */}
          <div className="relative my-5">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-200" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="bg-white px-3 text-gray-400">또는 소셜 로그인</span>
            </div>
          </div>

          <div className="space-y-3">
            <a
              href={`${BACKEND}/api/v1/auth/google`}
              className="flex items-center justify-center gap-3 w-full py-2.5 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <svg viewBox="0 0 24 24" className="w-5 h-5">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              구글로 로그인
            </a>

            <a
              href={`${BACKEND}/api/v1/auth/naver`}
              className="flex items-center justify-center gap-3 w-full py-2.5 px-4 bg-[#03C75A] text-white rounded-lg text-sm font-medium hover:bg-[#02b350] transition-colors"
            >
              <span className="w-5 h-5 flex items-center justify-center bg-white rounded-sm text-[#03C75A] font-extrabold text-base leading-none">N</span>
              네이버로 로그인
            </a>
          </div>

          <div className="mt-4 text-center">
            <Link to="/forgot-password" className="text-sm text-gray-500 hover:text-primary-600">
              비밀번호를 잊으셨나요?
            </Link>
          </div>

          <div className="mt-2 text-center text-sm text-gray-500">
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
