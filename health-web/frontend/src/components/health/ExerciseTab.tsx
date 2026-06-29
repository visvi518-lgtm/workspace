import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, ChevronDown, ChevronUp, CheckSquare, Trash2 } from 'lucide-react';
import { healthApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { ExerciseLog, ExerciseItem } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const PURPOSE_OPTIONS = [
  { value: 'posture', label: '체형교정' },
  { value: 'strength', label: '스트렝스' },
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

  const { data: logs = [] } = useQuery<ExerciseLog[]>({
    queryKey: ['exerciseLogs'],
    queryFn: () => healthApi.getExerciseLogs().then((r) => r.data),
  });

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
              <div className="grid grid-cols-5 gap-1 mb-2">
                {(['name', 'sets', 'reps', 'weight', 'duration_minutes'] as const).map((field) => (
                  <input
                    key={field}
                    type={field === 'name' ? 'text' : 'number'}
                    value={newEx[field]}
                    onChange={(e) => setNewEx({ ...newEx, [field]: e.target.value })}
                    placeholder={({ name: '종목명', sets: '세트', reps: '횟수', weight: 'kg', duration_minutes: '분' })[field]}
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
