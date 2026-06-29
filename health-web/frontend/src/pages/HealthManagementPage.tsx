import { useState } from 'react';
import { Dumbbell, Utensils, CalendarDays, Weight } from 'lucide-react';
import ExerciseTab from '@/components/health/ExerciseTab';
import DietTab from '@/components/health/DietTab';
import CalendarTab from '@/components/health/CalendarTab';
import WeightTab from '@/components/health/WeightTab';

type Tab = 'exercise' | 'diet' | 'calendar' | 'weight';

const tabs: { id: Tab; label: string; Icon: React.ElementType }[] = [
  { id: 'exercise', label: '운동관리', Icon: Dumbbell },
  { id: 'diet', label: '식단관리', Icon: Utensils },
  { id: 'calendar', label: '캘린더', Icon: CalendarDays },
  { id: 'weight', label: '체중기록', Icon: Weight },
];

export default function HealthManagementPage() {
  const [active, setActive] = useState<Tab>('exercise');

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">운동 및 식단 기록</h1>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setActive(id)}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all
              ${active === id
                ? 'bg-white text-primary-700 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'}`}
          >
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      {active === 'exercise' && <ExerciseTab />}
      {active === 'diet' && <DietTab />}
      {active === 'calendar' && <CalendarTab />}
      {active === 'weight' && <WeightTab />}
    </div>
  );
}
