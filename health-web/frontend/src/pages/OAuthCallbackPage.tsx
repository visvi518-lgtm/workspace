import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { authApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

const ERROR_MESSAGES: Record<string, string> = {
  google_cancelled: '구글 로그인이 취소되었습니다.',
  google_failed: '구글 로그인에 실패했습니다.',
  google_info: '구글 계정 정보를 가져올 수 없습니다.',
  naver_cancelled: '네이버 로그인이 취소되었습니다.',
  naver_failed: '네이버 로그인에 실패했습니다.',
  naver_info: '네이버 계정 정보를 가져올 수 없습니다.',
};

export default function OAuthCallbackPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  useEffect(() => {
    const token = params.get('token');
    const error = params.get('error');

    if (error) {
      toast.error(ERROR_MESSAGES[error] ?? '소셜 로그인에 실패했습니다.');
      navigate('/login');
      return;
    }

    if (!token) {
      navigate('/login');
      return;
    }

    authApi
      .meWithToken(token)
      .then((res) => {
        setAuth(res.data, token);
        toast.success(`${res.data.nickname}님, 환영합니다!`);
        navigate('/');
      })
      .catch(() => {
        toast.error('로그인 처리 중 오류가 발생했습니다.');
        navigate('/login');
      });
  }, []);

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center">
      <div className="flex flex-col items-center gap-3 text-gray-500">
        <Heart className="w-8 h-8 text-primary-500 fill-current animate-pulse" />
        <p className="text-sm">로그인 처리 중...</p>
      </div>
    </div>
  );
}
