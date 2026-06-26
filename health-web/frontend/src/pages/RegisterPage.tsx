import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';
import { authApi } from '@/services/api';
import toast from 'react-hot-toast';

const PW_REGEX = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,20}$/;

function PasswordRule({ ok, text }: { ok: boolean; text: string }) {
  return (
    <span className={`flex items-center gap-1 text-xs ${ok ? 'text-green-600' : 'text-gray-400'}`}>
      {ok ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {text}
    </span>
  );
}

export default function RegisterPage() {
  const [form, setForm] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    nickname: '',
    name: '',
  });
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const pw = form.password;
  const pwRules = {
    hasLetter: /[a-zA-Z]/.test(pw),
    hasNumber: /\d/.test(pw),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(pw),
    hasLength: pw.length >= 8 && pw.length <= 20,
  };
  const pwMatch = pw === form.passwordConfirm && pw.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!PW_REGEX.test(pw)) {
      toast.error('비밀번호 형식을 확인해 주세요.');
      return;
    }
    if (!pwMatch) {
      toast.error('비밀번호가 일치하지 않습니다.');
      return;
    }
    setLoading(true);
    try {
      await authApi.register({
        email: form.email,
        password: form.password,
        nickname: form.nickname,
        name: form.name || undefined,
      });
      toast.success('회원가입이 완료되었습니다. 로그인해 주세요.');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || '회원가입에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center py-8">
      <div className="w-full max-w-md">
        <div className="card">
          <div className="flex flex-col items-center mb-8">
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mb-3">
              <Heart className="w-6 h-6 text-primary-600 fill-current" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">회원가입</h1>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">이메일 *</label>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">닉네임 *</label>
              <input
                type="text"
                required
                minLength={2}
                maxLength={20}
                value={form.nickname}
                onChange={(e) => setForm({ ...form, nickname: e.target.value })}
                placeholder="닉네임 (2~20자)"
                className="input-base"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">이름 (선택)</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="실명"
                className="input-base"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호 *</label>
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
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {pw.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  <PasswordRule ok={pwRules.hasLetter} text="영문" />
                  <PasswordRule ok={pwRules.hasNumber} text="숫자" />
                  <PasswordRule ok={pwRules.hasSpecial} text="특수문자" />
                  <PasswordRule ok={pwRules.hasLength} text="8~20자" />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">비밀번호 확인 *</label>
              <input
                type="password"
                required
                value={form.passwordConfirm}
                onChange={(e) => setForm({ ...form, passwordConfirm: e.target.value })}
                placeholder="비밀번호 재입력"
                className={`input-base ${form.passwordConfirm && !pwMatch ? 'border-red-400 focus:ring-red-400' : ''}`}
              />
              {form.passwordConfirm && !pwMatch && (
                <p className="text-xs text-red-500 mt-1">비밀번호가 일치하지 않습니다.</p>
              )}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 mt-2">
              {loading ? '처리 중...' : '회원가입'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-500">
            이미 계정이 있으신가요?{' '}
            <Link to="/login" className="text-primary-600 font-medium hover:underline">
              로그인
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
