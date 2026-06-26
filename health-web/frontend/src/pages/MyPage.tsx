import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { User, Lock, Activity, Utensils } from 'lucide-react';
import { authApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

const NATIONALITY_OPTIONS = [{ value: 'korean', label: '내국인' }, { value: 'foreign', label: '외국인' }];
const EXERCISE_OPTIONS = [{ value: 'posture', label: '체형교정' }, { value: 'strength', label: '스트렝스' }, { value: 'weight_management', label: '체중관리' }];
const DIET_OPTIONS = [{ value: 'loss', label: '체중감소' }, { value: 'gain', label: '벌크업' }, { value: 'maintain', label: '유지' }, { value: 'medical', label: '건강상이유' }];

export default function MyPage() {
  const { user, updateUser } = useAuthStore();
  const [profileForm, setProfileForm] = useState({
    nickname: user?.nickname ?? '',
    name: user?.name ?? '',
    height: user?.profile?.height?.toString() ?? '',
    weight: user?.profile?.weight?.toString() ?? '',
    medical_history: user?.profile?.medical_history ?? '',
    medications: user?.profile?.medications ?? '',
    exercise_habits: user?.profile?.exercise_habits ?? '',
    nationality: user?.profile?.nationality ?? 'korean',
    exercise_purpose: user?.profile?.exercise_purpose ?? '',
    diet_purpose: user?.profile?.diet_purpose ?? '',
  });
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm: '' });
  const [activeSection, setActiveSection] = useState<'profile' | 'password'>('profile');

  const PW_REGEX = /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,20}$/;

  const profileMutation = useMutation({
    mutationFn: () => authApi.updateProfile({
      nickname: profileForm.nickname,
      name: profileForm.name || null,
      profile: {
        height: profileForm.height ? Number(profileForm.height) : null,
        weight: profileForm.weight ? Number(profileForm.weight) : null,
        medical_history: profileForm.medical_history || null,
        medications: profileForm.medications || null,
        exercise_habits: profileForm.exercise_habits || null,
        nationality: profileForm.nationality,
        exercise_purpose: profileForm.exercise_purpose || null,
        diet_purpose: profileForm.diet_purpose || null,
      },
    }),
    onSuccess: (res) => {
      updateUser(res.data);
      toast.success('프로필이 업데이트되었습니다.');
    },
    onError: (err: any) => toast.error(err.response?.data?.detail ?? '업데이트 실패'),
  });

  const pwMutation = useMutation({
    mutationFn: () => authApi.changePassword({
      current_password: pwForm.current_password,
      new_password: pwForm.new_password,
    }),
    onSuccess: () => {
      toast.success('비밀번호가 변경되었습니다.');
      setPwForm({ current_password: '', new_password: '', confirm: '' });
    },
    onError: (err: any) => toast.error(err.response?.data?.detail ?? '비밀번호 변경 실패'),
  });

  const handlePwSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!PW_REGEX.test(pwForm.new_password)) {
      toast.error('비밀번호 형식을 확인해 주세요. (영문+숫자+특수문자, 8~20자)');
      return;
    }
    if (pwForm.new_password !== pwForm.confirm) {
      toast.error('새 비밀번호가 일치하지 않습니다.');
      return;
    }
    pwMutation.mutate();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">마이페이지</h1>

      {/* Section tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveSection('profile')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${activeSection === 'profile' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
        >
          <User className="w-4 h-4" /> 프로필 수정
        </button>
        <button
          onClick={() => setActiveSection('password')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
            ${activeSection === 'password' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
        >
          <Lock className="w-4 h-4" /> 비밀번호 변경
        </button>
      </div>

      {activeSection === 'profile' && (
        <form onSubmit={(e) => { e.preventDefault(); profileMutation.mutate(); }} className="card space-y-4">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <User className="w-5 h-5 text-primary-600" /> 기본 정보
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">닉네임 *</label>
              <input type="text" value={profileForm.nickname} onChange={(e) => setProfileForm({ ...profileForm, nickname: e.target.value })} className="input-base" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">이름</label>
              <input type="text" value={profileForm.name} onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })} className="input-base" />
            </div>
          </div>

          <hr className="border-gray-100" />
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-600" /> 신체 정보 (선택)
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">키 (cm)</label>
              <input type="number" step="0.1" min="100" max="250" value={profileForm.height} onChange={(e) => setProfileForm({ ...profileForm, height: e.target.value })} className="input-base" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">체중 (kg)</label>
              <input type="number" step="0.1" min="20" max="300" value={profileForm.weight} onChange={(e) => setProfileForm({ ...profileForm, weight: e.target.value })} className="input-base" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">국적</label>
            <div className="flex gap-3">
              {NATIONALITY_OPTIONS.map((o) => (
                <label key={o.value} className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" value={o.value} checked={profileForm.nationality === o.value} onChange={() => setProfileForm({ ...profileForm, nationality: o.value as 'korean' | 'foreign' })} className="text-primary-600" />
                  <span className="text-sm">{o.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">과거 병력</label>
            <textarea rows={2} value={profileForm.medical_history} onChange={(e) => setProfileForm({ ...profileForm, medical_history: e.target.value })} placeholder="예: 고혈압, 당뇨 등" className="input-base resize-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">복용 약품</label>
            <textarea rows={2} value={profileForm.medications} onChange={(e) => setProfileForm({ ...profileForm, medications: e.target.value })} placeholder="예: 혈압약, 당뇨약 등" className="input-base resize-none" />
          </div>

          <hr className="border-gray-100" />
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Utensils className="w-5 h-5 text-primary-600" /> 목표 설정 (선택)
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">운동 목적</label>
              <div className="space-y-1">
                {EXERCISE_OPTIONS.map((o) => (
                  <label key={o.value} className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" value={o.value} checked={profileForm.exercise_purpose === o.value} onChange={() => setProfileForm({ ...profileForm, exercise_purpose: o.value })} className="text-primary-600" />
                    <span className="text-sm">{o.label}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">식단 목적</label>
              <div className="space-y-1">
                {DIET_OPTIONS.map((o) => (
                  <label key={o.value} className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" value={o.value} checked={profileForm.diet_purpose === o.value} onChange={() => setProfileForm({ ...profileForm, diet_purpose: o.value })} className="text-primary-600" />
                    <span className="text-sm">{o.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <button type="submit" disabled={profileMutation.isPending} className="btn-primary w-full">
            {profileMutation.isPending ? '저장 중...' : '저장하기'}
          </button>
        </form>
      )}

      {activeSection === 'password' && (
        <form onSubmit={handlePwSubmit} className="card space-y-4">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Lock className="w-5 h-5 text-primary-600" /> 비밀번호 변경
          </h2>
          {[
            { label: '현재 비밀번호', key: 'current_password' },
            { label: '새 비밀번호', key: 'new_password' },
            { label: '새 비밀번호 확인', key: 'confirm' },
          ].map(({ label, key }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                type="password"
                value={pwForm[key as keyof typeof pwForm]}
                onChange={(e) => setPwForm({ ...pwForm, [key]: e.target.value })}
                required
                className="input-base"
              />
            </div>
          ))}
          <p className="text-xs text-gray-500">영문, 숫자, 특수문자 포함 8~20자</p>
          <button type="submit" disabled={pwMutation.isPending} className="btn-primary w-full">
            {pwMutation.isPending ? '변경 중...' : '비밀번호 변경'}
          </button>
        </form>
      )}
    </div>
  );
}
