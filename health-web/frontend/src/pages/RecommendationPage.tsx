import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ChevronUp, Dumbbell, Salad, Clock, Flame, Search } from 'lucide-react';
import { recommendationApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import type { ExerciseRoutine, DietRecommendation, ExercisePurpose, DietPurpose, ExerciseCalorie } from '@/types';

// ── Label maps ────────────────────────────────────────────────────────────────

const EXERCISE_PURPOSE_LABELS: Record<ExercisePurpose, string> = {
  posture: '자세 교정',
  strength: '근력 향상',
  weight_management: '체중 관리',
};

const DIET_PURPOSE_LABELS: Record<DietPurpose, string> = {
  loss: '체중 감량',
  gain: '체중 증량',
  maintain: '체중 유지',
  medical: '의료 목적',
};

const DIFFICULTY_LABELS: Record<string, string> = {
  beginner: '초급',
  intermediate: '중급',
  advanced: '고급',
};

const DIFFICULTY_COLOR: Record<string, string> = {
  beginner: 'bg-green-100 text-green-700',
  intermediate: 'bg-yellow-100 text-yellow-700',
  advanced: 'bg-red-100 text-red-700',
};

// ── Exercise card ─────────────────────────────────────────────────────────────

function ExerciseCard({ routine }: { routine: ExerciseRoutine }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card border border-gray-100 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-primary-100 text-primary-700">
              {EXERCISE_PURPOSE_LABELS[routine.purpose]}
            </span>
            {routine.difficulty && (
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${DIFFICULTY_COLOR[routine.difficulty] ?? 'bg-gray-100 text-gray-600'}`}>
                {DIFFICULTY_LABELS[routine.difficulty] ?? routine.difficulty}
              </span>
            )}
          </div>
          <h3 className="font-semibold text-gray-900">{routine.name}</h3>
          {routine.description && (
            <p className="text-sm text-gray-500 mt-1 leading-relaxed">{routine.description}</p>
          )}
          <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
            <Clock className="w-3.5 h-3.5" />
            <span>주 {routine.sessions_per_week}회 · {routine.exercises.length}가지 운동</span>
          </div>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors"
        >
          {open ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {open && routine.exercises.length > 0 && (
        <div className="border-t border-gray-100 pt-3">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                  <th className="pb-2 pr-3 font-medium">운동명</th>
                  <th className="pb-2 pr-3 font-medium whitespace-nowrap">세트</th>
                  <th className="pb-2 pr-3 font-medium whitespace-nowrap">횟수/시간</th>
                  <th className="pb-2 pr-3 font-medium whitespace-nowrap">휴식</th>
                  <th className="pb-2 font-medium">메모</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {routine.exercises.map((ex, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="py-2 pr-3 font-medium text-gray-800">{ex.name}</td>
                    <td className="py-2 pr-3 text-gray-600 whitespace-nowrap">{ex.sets}</td>
                    <td className="py-2 pr-3 text-gray-600 whitespace-nowrap">{ex.reps}</td>
                    <td className="py-2 pr-3 text-gray-600 whitespace-nowrap">{ex.rest}</td>
                    <td className="py-2 text-gray-400 text-xs">{ex.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Macro ratio bar ───────────────────────────────────────────────────────────

function MacroBar({ carb, protein, fat }: { carb: number; protein: number; fat: number }) {
  return (
    <div className="space-y-2">
      <div className="flex rounded-full overflow-hidden h-4 text-xs font-medium">
        <div style={{ width: `${carb}%` }} className="bg-amber-400 flex items-center justify-center text-white">
          {carb >= 15 ? `${carb}%` : ''}
        </div>
        <div style={{ width: `${protein}%` }} className="bg-primary-500 flex items-center justify-center text-white">
          {protein >= 15 ? `${protein}%` : ''}
        </div>
        <div style={{ width: `${fat}%` }} className="bg-rose-400 flex items-center justify-center text-white">
          {fat >= 15 ? `${fat}%` : ''}
        </div>
      </div>
      <div className="flex gap-4 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />탄수화물 {carb}%</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-primary-500 inline-block" />단백질 {protein}%</span>
        <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-rose-400 inline-block" />지방 {fat}%</span>
      </div>
    </div>
  );
}

// ── Diet card ─────────────────────────────────────────────────────────────────

function DietCard({ rec }: { rec: DietRecommendation }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card border border-gray-100 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700">
              {DIET_PURPOSE_LABELS[rec.purpose]}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900">{rec.name}</h3>
          {rec.description && (
            <p className="text-sm text-gray-500 mt-1 leading-relaxed">{rec.description}</p>
          )}
          {rec.calorie_note && (
            <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
              <Flame className="w-3.5 h-3.5" />
              <span>{rec.calorie_note}</span>
            </div>
          )}
          <div className="mt-3">
            <MacroBar carb={rec.carb_ratio} protein={rec.protein_ratio} fat={rec.fat_ratio} />
          </div>
        </div>
        <button
          onClick={() => setOpen(!open)}
          className="flex-shrink-0 p-2 rounded-lg hover:bg-gray-100 text-gray-400 transition-colors"
        >
          {open ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {open && rec.nutrients.length > 0 && (
        <div className="border-t border-gray-100 pt-3 space-y-2">
          <p className="text-xs font-medium text-gray-500 mb-2">영양소별 권장 섭취량</p>
          {rec.nutrients.map((n, i) => (
            <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
              <div className="w-28 flex-shrink-0">
                <span className="text-sm font-medium text-gray-800">{n.name}</span>
              </div>
              <div className="flex-1">
                <span className="text-sm text-primary-700 font-medium">{n.target}</span>
                {n.unit && <span className="text-xs text-gray-400 ml-1">{n.unit}</span>}
                {n.notes && <p className="text-xs text-gray-400 mt-0.5">{n.notes}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

type MainTab = 'exercise' | 'diet' | 'calorie';

const CALORIE_CATEGORIES = ['전체', '유산소', '근력', '스포츠', '기타'];

export default function RecommendationPage() {
  const user = useAuthStore((s) => s.user);
  const [tab, setTab] = useState<MainTab>('exercise');

  const userExercisePurpose = (user?.profile?.exercise_purpose as ExercisePurpose | undefined);
  const userDietPurpose = (user?.profile?.diet_purpose as DietPurpose | undefined);
  const profileWeight = user?.profile?.weight;

  const [exercisePurpose, setExercisePurpose] = useState<ExercisePurpose | ''>(
    userExercisePurpose ?? ''
  );
  const [dietPurpose, setDietPurpose] = useState<DietPurpose | ''>(
    userDietPurpose ?? ''
  );

  // Calorie calculator state
  const [calCategory, setCalCategory] = useState('전체');
  const [calSearch, setCalSearch] = useState('');
  const [selectedExercise, setSelectedExercise] = useState<ExerciseCalorie | null>(null);
  const [duration, setDuration] = useState(30);
  const [weight, setWeight] = useState(profileWeight ?? 70);

  const { data: exerciseData = [], isLoading: exLoading } = useQuery<ExerciseRoutine[]>({
    queryKey: ['recommendations', 'exercise', exercisePurpose],
    queryFn: () =>
      recommendationApi.getExercise(exercisePurpose || undefined).then((r) => r.data),
  });

  const { data: dietData = [], isLoading: dietLoading } = useQuery<DietRecommendation[]>({
    queryKey: ['recommendations', 'diet', dietPurpose],
    queryFn: () =>
      recommendationApi.getDiet(dietPurpose || undefined).then((r) => r.data),
  });

  const { data: calorieData = [], isLoading: calLoading } = useQuery<ExerciseCalorie[]>({
    queryKey: ['exercise-calories'],
    queryFn: () => recommendationApi.getExerciseCalories().then((r) => r.data),
    enabled: tab === 'calorie',
  });

  const filteredCalories = useMemo(() => {
    let list = calorieData;
    if (calCategory !== '전체') list = list.filter((c) => c.category === calCategory);
    if (calSearch.trim()) {
      const q = calSearch.trim().toLowerCase();
      list = list.filter((c) => c.name.toLowerCase().includes(q) || (c.description ?? '').toLowerCase().includes(q));
    }
    return list;
  }, [calorieData, calCategory, calSearch]);

  const calculatedCalories = selectedExercise
    ? Math.round(selectedExercise.met * weight * (duration / 60))
    : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">맞춤 추천</h1>
        <p className="text-sm text-gray-500 mt-1">목적에 맞는 운동 루틴과 식단을 확인하세요.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <button
          onClick={() => setTab('exercise')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors
            ${tab === 'exercise' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
        >
          <Dumbbell className="w-4 h-4" /> 운동 루틴
        </button>
        <button
          onClick={() => setTab('diet')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors
            ${tab === 'diet' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
        >
          <Salad className="w-4 h-4" /> 식단 추천
        </button>
        <button
          onClick={() => setTab('calorie')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium transition-colors
            ${tab === 'calorie' ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
        >
          <Flame className="w-4 h-4" /> 칼로리 계산
        </button>
      </div>

      {/* ─── Exercise Tab ─── */}
      {tab === 'exercise' && (
        <div className="space-y-4">
          {/* Purpose filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setExercisePurpose('')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
                ${exercisePurpose === '' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
            >
              전체
            </button>
            {(Object.entries(EXERCISE_PURPOSE_LABELS) as [ExercisePurpose, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setExercisePurpose(key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
                  ${exercisePurpose === key ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
              >
                {label}
                {key === userExercisePurpose && <span className="ml-1 text-xs opacity-75">(내 목적)</span>}
              </button>
            ))}
          </div>

          {exLoading ? (
            <div className="text-center py-12 text-gray-400 text-sm">불러오는 중...</div>
          ) : exerciseData.length === 0 ? (
            <div className="card text-center py-12 text-gray-400">
              <Dumbbell className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">등록된 운동 루틴이 없습니다.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {exerciseData.map((r) => <ExerciseCard key={r.id} routine={r} />)}
            </div>
          )}
        </div>
      )}

      {/* ─── Diet Tab ─── */}
      {tab === 'diet' && (
        <div className="space-y-4">
          {/* Purpose filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setDietPurpose('')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
                ${dietPurpose === '' ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
            >
              전체
            </button>
            {(Object.entries(DIET_PURPOSE_LABELS) as [DietPurpose, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setDietPurpose(key)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
                  ${dietPurpose === key ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
              >
                {label}
                {key === userDietPurpose && <span className="ml-1 text-xs opacity-75">(내 목적)</span>}
              </button>
            ))}
          </div>

          {dietLoading ? (
            <div className="text-center py-12 text-gray-400 text-sm">불러오는 중...</div>
          ) : dietData.length === 0 ? (
            <div className="card text-center py-12 text-gray-400">
              <Salad className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">등록된 식단 추천이 없습니다.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {dietData.map((r) => <DietCard key={r.id} rec={r} />)}
            </div>
          )}
        </div>
      )}

      {/* ─── Calorie Calculator Tab ─── */}
      {tab === 'calorie' && (
        <div className="space-y-4">
          {/* Calculator card */}
          <div className="card border border-orange-100 space-y-4">
            <div className="flex items-center gap-2">
              <Flame className="w-5 h-5 text-orange-500" />
              <h2 className="font-semibold text-gray-900">운동 칼로리 계산기</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">체중 (kg)</label>
                <input
                  type="number" min="30" max="200" step="0.5"
                  value={weight}
                  onChange={(e) => setWeight(Number(e.target.value))}
                  className="input-base text-sm"
                />
                {profileWeight && weight !== profileWeight && (
                  <button
                    onClick={() => setWeight(profileWeight)}
                    className="text-xs text-primary-600 mt-1 hover:underline"
                  >
                    프로필 체중으로 ({profileWeight}kg)
                  </button>
                )}
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">운동 시간 (분)</label>
                <input
                  type="number" min="1" max="300" step="5"
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  className="input-base text-sm"
                />
              </div>
            </div>

            {selectedExercise ? (
              <div className="rounded-xl bg-orange-50 border border-orange-200 p-4 flex items-center gap-4">
                <div className="flex-1">
                  <p className="text-xs text-orange-600 font-medium">{selectedExercise.category}</p>
                  <p className="font-semibold text-gray-900">{selectedExercise.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">MET {selectedExercise.met} · {duration}분 · {weight}kg</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-orange-500">{calculatedCalories}</p>
                  <p className="text-xs text-gray-500">kcal 소모</p>
                </div>
                <button
                  onClick={() => setSelectedExercise(null)}
                  className="text-xs text-gray-400 hover:text-gray-600 self-start"
                >✕</button>
              </div>
            ) : (
              <p className="text-sm text-gray-400 text-center py-2">
                아래 목록에서 운동을 선택하면 칼로리가 계산됩니다.
              </p>
            )}
          </div>

          {/* Exercise list */}
          <div className="space-y-3">
            {/* Category filter */}
            <div className="flex flex-wrap gap-2">
              {CALORIE_CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCalCategory(cat)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
                    ${calCategory === cat ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" />
              <input
                type="text"
                value={calSearch}
                onChange={(e) => setCalSearch(e.target.value)}
                placeholder="운동명으로 검색..."
                className="input-base text-sm pl-9"
              />
            </div>

            {calLoading ? (
              <div className="text-center py-12 text-gray-400 text-sm">불러오는 중...</div>
            ) : filteredCalories.length === 0 ? (
              <div className="card text-center py-12 text-gray-400">
                <Flame className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">검색 결과가 없습니다.</p>
              </div>
            ) : (
              <div className="grid gap-2 sm:grid-cols-2">
                {filteredCalories.map((c) => {
                  const isSelected = selectedExercise?.id === c.id;
                  const kcal = Math.round(c.met * weight * (duration / 60));
                  return (
                    <button
                      key={c.id}
                      onClick={() => setSelectedExercise(isSelected ? null : c)}
                      className={`text-left rounded-xl border p-3 transition-all hover:border-orange-300 ${
                        isSelected ? 'border-orange-400 bg-orange-50' : 'border-gray-100 bg-white hover:bg-orange-50/50'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <span className="text-xs px-1.5 py-0.5 rounded bg-orange-100 text-orange-700 font-medium">{c.category}</span>
                          <p className="text-sm font-medium text-gray-800 mt-1 leading-tight">{c.name}</p>
                          {c.description && <p className="text-xs text-gray-400 mt-0.5 truncate">{c.description}</p>}
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-base font-bold text-orange-500">{kcal}</p>
                          <p className="text-xs text-gray-400">kcal/{duration}분</p>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
