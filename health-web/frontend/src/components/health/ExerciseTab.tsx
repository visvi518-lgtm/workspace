import { useState, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, ChevronDown, ChevronUp, CheckSquare, Trash2, Search } from 'lucide-react';
import { healthApi, recommendationApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { ExerciseLog, ExerciseItem, ExerciseCalorie } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const PURPOSE_OPTIONS = [
  { value: 'posture', label: '체형교정' },
  { value: 'strength', label: '근력향상' },
  { value: 'weight_management', label: '체중관리' },
];

export default function ExerciseTab() {
  const { user, updateUser } = useAuthStore();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [today] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [form, setForm] = useState({ date: today, content: '', duration_minutes: 30, exercises: [] as ExerciseItem[] });
  const [newEx, setNewEx] = useState({ name: '', sets: '', reps: '', weight: '', duration_minutes: '' });
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [showExDropdown, setShowExDropdown] = useState(false);
  const nameInputRef = useRef<HTMLInputElement>(null);

  const { data: logs = [] } = useQuery<ExerciseLog[]>({
    queryKey: ['exerciseLogs'],
    queryFn: () => healthApi.getExerciseLogs().then((r) => r.data),
  });

  const { data: exerciseCalories = [] } = useQuery<ExerciseCalorie[]>({
    queryKey: ['exerciseCalories'],
    queryFn: () => recommendationApi.getExerciseCalories().then((r) => r.data),
    enabled: showForm,
    staleTime: 5 * 60 * 1000,
  });

  const PURPOSE_CATEGORY: Record<string, string> = {
    strength: '근력',
    weight_management: '유산소',
    posture: '기타',
  };

  const calDropdownList = useMemo(() => {
    const q = newEx.name.trim().toLowerCase();
    if (q) {
      // 검색어 있으면 전체 종목에서 검색
      return exerciseCalories
        .filter((c) => c.name.toLowerCase().includes(q) || c.category.includes(q))
        .slice(0, 10);
    }
    // 검색어 없으면 운동 목적에 맞는 카테고리 우선
    const purposeCategory = PURPOSE_CATEGORY[user?.profile?.exercise_purpose ?? ''];
    const list = purposeCategory
      ? exerciseCalories.filter((c) => c.category === purposeCategory)
      : exerciseCalories;
    return list.slice(0, 10);
  }, [exerciseCalories, newEx.name, user?.profile?.exercise_purpose]);

  const createMutation = useMutation({
    mutationFn: () => healthApi.createExerciseLog(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['exerciseLogs'] });
      setShowForm(false);
      setForm({ date: today, content: '', duration_minutes: 30, exercises: [] });
      toast.success('운동일지가 저장되었습니다.');
    },
  });

  const updatePurpose = async (purpose: string) => {
    try {
      await healthApi.updateUserHealthProfile({ exercise_purpose: purpose });
      if (user) {
        updateUser({ ...user, profile: { ...user.profile, exercise_purpose: purpose as any } });
      }
      toast.success('운동 목적이 업데이트되었습니다.');
    } catch {
      toast.error('업데이트에 실패했습니다.');
    }
  };

  const addExercise = () => {
    if (!newEx.name.trim()) return;
    setForm({
      ...form,
      exercises: [
        ...form.exercises,
        {
          name: newEx.name,
          sets: newEx.sets ? Number(newEx.sets) : undefined,
          reps: newEx.reps ? Number(newEx.reps) : undefined,
          weight: newEx.weight ? Number(newEx.weight) : undefined,
          duration_minutes: newEx.duration_minutes ? Number(newEx.duration_minutes) : undefined,
        },
      ],
    });
    setNewEx({ name: '', sets: '', reps: '', weight: '', duration_minutes: '' });
  };

  return (
    <div className="space-y-6">
      {/* Purpose */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-3">운동 목적</h2>
        <div className="flex flex-wrap gap-2">
          {PURPOSE_OPTIONS.map((o) => (
            <button
              key={o.value}
              onClick={() => updatePurpose(o.value)}
              className={`px-4 py-2 rounded-lg border-2 text-sm font-medium transition-colors
                ${user?.profile?.exercise_purpose === o.value
                  ? 'border-primary-600 bg-primary-50 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:border-primary-300'}`}
            >
              {o.label}
              {user?.profile?.exercise_purpose === o.value && (
                <CheckSquare className="inline w-4 h-4 ml-1" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Add log */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">운동일지</h2>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-1">
            <Plus className="w-4 h-4" /> 기록추가
          </button>
        </div>

        {showForm && (
          <div className="border border-primary-200 rounded-xl p-4 mb-4 space-y-3 bg-primary-50">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">날짜</label>
                <input
                  type="date"
                  value={form.date}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                  className="input-base"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600 mb-1 block">총 운동시간 (분)</label>
                <input
                  type="number"
                  min={1}
                  value={form.duration_minutes}
                  onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })}
                  className="input-base"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">메모</label>
              <textarea
                rows={2}
                value={form.content}
                onChange={(e) => setForm({ ...form, content: e.target.value })}
                placeholder="오늘 운동 메모"
                className="input-base resize-none"
              />
            </div>

            {/* Exercise items */}
            <div>
              <label className="text-xs font-medium text-gray-600 mb-2 block">운동 종목</label>

              {/* 종목명 검색 */}
              <div className="relative mb-1">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-300 pointer-events-none" />
                <input
                  ref={nameInputRef}
                  type="text"
                  value={newEx.name}
                  onChange={(e) => {
                    setNewEx({ ...newEx, name: e.target.value });
                    setShowExDropdown(true);
                  }}
                  onFocus={() => setShowExDropdown(true)}
                  onBlur={() => setTimeout(() => setShowExDropdown(false), 150)}
                  placeholder="종목명 검색 또는 직접 입력"
                  className="input-base text-sm pl-8 w-full"
                />
                {showExDropdown && calDropdownList.length > 0 && (
                  <ul className="absolute z-20 left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg max-h-48 overflow-y-auto">
                    {!newEx.name.trim() && PURPOSE_CATEGORY[user?.profile?.exercise_purpose ?? ''] && (
                      <li className="px-3 py-1.5 text-xs text-gray-400 bg-gray-50 border-b border-gray-100">
                        {PURPOSE_CATEGORY[user!.profile!.exercise_purpose!]} 종목 · 검색하면 전체 표시
                      </li>
                    )}
                    {calDropdownList.map((c) => (
                      <li key={c.id}>
                        <button
                          type="button"
                          onMouseDown={() => {
                            setNewEx({ ...newEx, name: c.name });
                            setShowExDropdown(false);
                            nameInputRef.current?.blur();
                          }}
                          className="w-full text-left px-3 py-2 hover:bg-primary-50 flex items-center justify-between gap-2"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 flex-shrink-0">{c.category}</span>
                            <span className="text-sm text-gray-800 truncate">{c.name}</span>
                          </div>
                          <span className="text-xs text-gray-400 flex-shrink-0">MET {c.met}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* 세트 / 횟수 / kg / 분 */}
              <div className="grid grid-cols-4 gap-1 mb-2">
                {(['sets', 'reps', 'weight', 'duration_minutes'] as const).map((field) => (
                  <input
                    key={field}
                    type="number"
                    value={newEx[field]}
                    onChange={(e) => setNewEx({ ...newEx, [field]: e.target.value })}
                    placeholder={({ sets: '세트', reps: '횟수', weight: 'kg', duration_minutes: '분' })[field]}
                    className="input-base text-sm py-1.5"
                    min={0}
                  />
                ))}
              </div>
              <button type="button" onClick={addExercise} className="btn-secondary text-sm w-full">
                + 종목 추가
              </button>
              {form.exercises.map((ex, i) => (
                <div key={i} className="flex items-center justify-between bg-white rounded-lg p-2 mt-1 text-sm">
                  <span className="font-medium">{ex.name}</span>
                  <span className="text-gray-500">
                    {ex.sets && `${ex.sets}세트`} {ex.reps && `${ex.reps}회`} {ex.weight && `${ex.weight}kg`}
                  </span>
                  <button onClick={() => setForm({ ...form, exercises: form.exercises.filter((_, j) => j !== i) })}>
                    <Trash2 className="w-3.5 h-3.5 text-red-400" />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex gap-2">
              <button onClick={() => setShowForm(false)} className="btn-secondary flex-1">취소</button>
              <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending} className="btn-primary flex-1">
                저장
              </button>
            </div>
          </div>
        )}

        {/* Log list */}
        <div className="space-y-2">
          {logs.length === 0 && (
            <p className="text-center text-gray-400 py-8 text-sm">운동일지를 작성해 보세요!</p>
          )}
          {logs.map((log) => (
            <div key={log.id} className="border border-gray-100 rounded-lg overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50"
                onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-900">{log.date}</span>
                  <span className="text-xs text-gray-500">{log.duration_minutes}분</span>
                  <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                    {log.exercises.length}종목
                  </span>
                </div>
                {expandedId === log.id ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
              </button>
              {expandedId === log.id && (
                <div className="px-4 pb-3 text-sm space-y-2 bg-gray-50">
                  {log.content && <p className="text-gray-600 py-2">{log.content}</p>}
                  {log.exercises.map((ex, i) => (
                    <div key={i} className="flex items-center justify-between bg-white rounded p-2">
                      <span className="font-medium">{ex.name}</span>
                      <span className="text-gray-500 text-xs">
                        {[ex.sets && `${ex.sets}세트`, ex.reps && `${ex.reps}회`, ex.weight && `${ex.weight}kg`].filter(Boolean).join(' · ')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
