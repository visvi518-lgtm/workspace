import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Heart, ArrowLeft } from 'lucide-react';
import { authApi } from '@/services/api';
import toast from 'react-hot-toast';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authApi.forgotPassword(email);
      setSent(true);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '요청에 실패했습니다.');
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
            <h1 className="text-2xl font-bold text-gray-900">비밀번호 찾기</h1>
            <p className="text-sm text-gray-500 mt-1">가입한 이메일로 재설정 링크를 보내드립니다</p>
          </div>

          {sent ? (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-gray-700 font-medium">이메일을 확인해 주세요</p>
              <p className="text-sm text-gray-500">
                <span className="font-medium text-gray-700">{email}</span>로<br />
                비밀번호 재설정 링크를 발송했습니다.<br />
                링크는 1시간 후 만료됩니다.
              </p>
              <Link to="/login" className="btn-primary inline-block mt-2">
                로그인으로 돌아가기
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="가입한 이메일 주소"
                  className="input-base"
                />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
                {loading ? '발송 중...' : '재설정 링크 보내기'}
              </button>
            </form>
          )}

          {!sent && (
            <div className="mt-4 text-center">
              <Link to="/login" className="flex items-center justify-center gap-1 text-sm text-gray-500 hover:text-primary-600">
                <ArrowLeft className="w-4 h-4" /> 로그인으로 돌아가기
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
