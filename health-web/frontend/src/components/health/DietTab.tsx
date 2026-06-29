import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Camera, Flame, Trash2, CheckSquare } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { healthApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { DietLog } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const DIET_PURPOSE = [
  { value: 'loss', label: '체중감소' },
  { value: 'gain', label: '벌크업' },
  { value: 'maintain', label: '유지' },
  { value: 'medical', label: '건강상이유' },
];

const MEAL_TYPES = [
  { value: 'breakfast', label: '아침' },
  { value: 'lunch', label: '점심' },
  { value: 'dinner', label: '저녁' },
  { value: 'snack', label: '간식' },
];

export default function DietTab() {
  const { user, updateUser } = useAuthStore();
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [today] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [form, setForm] = useState({ date: today, meals: [] as any[], note: '' });
  const [mealType, setMealType] = useState('breakfast');
  const [foodName, setFoodName] = useState('');
  const [foodCal, setFoodCal] = useState('');
  const [foodAmount, setFoodAmount] = useState('');
  const [analyzing, setAnalyzing] = useState(false);
  const [aiResult, setAiResult] = useState<{ name: string; calories: number; amount: string } | null>(null);

  const { data: logs = [] } = useQuery<DietLog[]>({
    queryKey: ['dietLogs'],
    queryFn: () => healthApi.getDietLogs().then((r) => r.data),
  });

  const createMutation = useMutation({
    mutationFn: () => healthApi.createDietLog(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['dietLogs'] });
      setShowForm(false);
      setForm({ date: today, meals: [], note: '' });
      toast.success('식단이 저장되었습니다.');
    },
  });

  const updateDietPurpose = async (purpose: string) => {
    try {
      await healthApi.updateUserHealthProfile({ diet_purpose: purpose });
      if (user) {
        updateUser({ ...user, profile: { ...user.profile, diet_purpose: purpose as any } });
      }
      toast.success('식단 목적이 업데이트되었습니다.');
    } catch {
      toast.error('업데이트에 실패했습니다.');
    }
  };

  const addFoodToMeal = (food: { name: string; calories: number; amount: string }) => {
    if (!food.name) return;
    const meals = [...form.meals];
    const idx = meals.findIndex((m) => m.meal_type === mealType);
    if (idx >= 0) {
      meals[idx] = { ...meals[idx], foods: [...meals[idx].foods, food] };
    } else {
      meals.push({ meal_type: mealType, foods: [food] });
    }
    setForm((prev: typeof form) => ({ ...prev, meals }));
  };

  const onDrop = useCallback(async (files: File[]) => {
    if (!files[0]) return;
    setAnalyzing(true);
    try {
      const fd = new FormData();
      fd.append('image', files[0]);
      const res = await healthApi.analyzeCalories(fd);
      setAiResult(res.data);
      // AI 분석 결과를 바로 식단에 자동 추가
      addFoodToMeal(res.data);
      toast.success(`칼로리 분석 완료! ${res.data.name} ${res.data.calories}kcal가 추가되었습니다.`);
    } catch {
      toast.error('이미지 분석에 실패했습니다.');
    } finally {
      setAnalyzing(false);
    }
  }, [mealType, form.meals]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': [] },
    maxFiles: 1,
  });

  const addFood = () => {
    const food = { name: foodName, calories: Number(foodCal), amount: foodAmount };
    if (!food.name) return;
    addFoodToMeal(food);
    setFoodName(''); setFoodCal(''); setFoodAmount('');
  };

  const totalCalories = form.meals.reduce((sum, m) => sum + m.foods.reduce((s: number, f: any) => s + f.calories, 0), 0);

  return (
    <div className="space-y-6">
      {/* Purpose */}
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-3">식단 목적</h2>
        <div className="flex flex-wrap gap-2">
          {DIET_PURPOSE.map((o) => (
            <button
              key={o.value}
              onClick={() => updateDietPurpose(o.value)}
              className={`px-4 py-2 rounded-lg border-2 text-sm font-medium transition-colors
                ${user?.profile?.diet_purpose === o.value
                  ? 'border-primary-600 bg-primary-50 text-primary-700'
                  : 'border-gray-200 text-gray-600 hover:border-primary-300'}`}
            >
              {o.label}
              {user?.profile?.diet_purpose === o.value && (
                <CheckSquare className="inline w-4 h-4 ml-1" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Add diet log */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">식단일지</h2>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary flex items-center gap-1">
            <Plus className="w-4 h-4" /> 기록추가
          </button>
        </div>

        {showForm && (
          <div className="border border-primary-200 rounded-xl p-4 mb-4 space-y-4 bg-primary-50">
            <div>
              <label className="text-xs font-medium text-gray-600 mb-1 block">날짜</label>
              <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className="input-base" />
            </div>

            {/* AI calorie analyzer */}
            <div>
              <label className="text-xs font-medium text-gray-600 mb-2 block flex items-center gap-1">
                <Camera className="w-3.5 h-3.5" /> 사진으로 칼로리 분석 (AI)
              </label>
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
                  ${isDragActive ? 'border-primary-400 bg-primary-100' : 'border-gray-300 hover:border-primary-300'}`}
              >
                <input {...getInputProps()} />
                {analyzing ? (
                  <p className="text-sm text-gray-500">분석 중...</p>
                ) : aiResult ? (
                  <div className="text-sm space-y-1">
                    <p className="text-xs text-green-600 font-medium">✓ 식단에 자동 추가됨</p>
                    <p className="font-medium text-gray-900">{aiResult.name}</p>
                    <p className="text-primary-600 font-bold">{aiResult.calories} kcal</p>
                    <p className="text-gray-500">{aiResult.amount}</p>
                    <p className="text-xs text-gray-400 mt-1">다른 사진을 클릭하여 추가 분석</p>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    음식 사진을 드래그하거나 클릭하여 업로드
                  </p>
                )}
              </div>
            </div>

            {/* Manual food entry */}
            <div>
              <label className="text-xs font-medium text-gray-600 mb-2 block">식사 유형 & 음식 추가</label>
              <div className="flex gap-1 mb-2">
                {MEAL_TYPES.map((m) => (
                  <button
                    key={m.value}
                    type="button"
                    onClick={() => setMealType(m.value)}
                    className={`flex-1 py-1.5 text-xs rounded-lg border transition-colors
                      ${mealType === m.value ? 'border-primary-500 bg-primary-100 text-primary-700' : 'border-gray-200 text-gray-600'}`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-2 mb-2">
                <input value={foodName} onChange={(e) => setFoodName(e.target.value)} placeholder="음식명" className="input-base text-sm" />
                <input type="number" value={foodCal} onChange={(e) => setFoodCal(e.target.value)} placeholder="kcal" className="input-base text-sm" min={0} />
                <input value={foodAmount} onChange={(e) => setFoodAmount(e.target.value)} placeholder="양 (eg. 1인분)" className="input-base text-sm" />
              </div>
              <button type="button" onClick={addFood} className="btn-secondary text-sm w-full">+ 음식 추가</button>
            </div>

            {/* Preview */}
            {form.meals.length > 0 && (
              <div className="bg-white rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between text-sm font-medium">
                  <span>총 칼로리</span>
                  <span className="text-primary-600 flex items-center gap-1">
                    <Flame className="w-4 h-4" /> {totalCalories} kcal
                  </span>
                </div>
                {form.meals.map((m, i) => (
                  <div key={i}>
                    <p className="text-xs font-medium text-gray-500 mb-1">
                      {MEAL_TYPES.find((t) => t.value === m.meal_type)?.label}
                    </p>
                    {m.foods.map((f: any, j: number) => (
                      <div key={j} className="flex items-center justify-between text-xs text-gray-700 py-0.5">
                        <span>{f.name} {f.amount && `(${f.amount})`}</span>
                        <span>{f.calories} kcal</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}

            <div className="flex gap-2">
              <button onClick={() => setShowForm(false)} className="btn-secondary flex-1">취소</button>
              <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending} className="btn-primary flex-1">저장</button>
            </div>
          </div>
        )}

        {/* Log list */}
        <div className="space-y-2">
          {logs.length === 0 && <p className="text-center text-gray-400 py-8 text-sm">식단을 기록해 보세요!</p>}
          {logs.map((log) => (
            <div key={log.id} className="border border-gray-100 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-900">{log.date}</span>
                <span className="text-sm text-primary-600 font-medium flex items-center gap-1">
                  <Flame className="w-3.5 h-3.5" /> {log.total_calories} kcal
                </span>
              </div>
              <div className="flex flex-wrap gap-1">
                {log.meals.map((m, i) => (
                  <span key={i} className="text-xs bg-gray-100 px-2 py-0.5 rounded-full text-gray-600">
                    {MEAL_TYPES.find((t) => t.value === m.meal_type)?.label}: {m.foods.map((f: any) => f.name).join(', ')}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
