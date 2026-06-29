import { useState } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { useQuery } from '@tanstack/react-query';
import { Dumbbell, Utensils } from 'lucide-react';
import { healthApi } from '@/services/api';
import { format } from 'date-fns';

type CalendarValue = Date | null | [Date | null, Date | null];

export default function CalendarTab() {
  const [date, setDate] = useState(new Date());
  const month = format(date, 'yyyy-MM');

  const { data: calData } = useQuery({
    queryKey: ['calendarData', month],
    queryFn: () => healthApi.getCalendarData(month).then((r) => r.data),
  });

  const exerciseDates: Set<string> = new Set(calData?.exercise_dates ?? []);
  const dietDates: Set<string> = new Set(calData?.diet_dates ?? []);

  const tileContent = ({ date: d }: { date: Date }) => {
    const ds = format(d, 'yyyy-MM-dd');
    const hasEx = exerciseDates.has(ds);
    const hasDiet = dietDates.has(ds);
    if (!hasEx && !hasDiet) return null;
    return (
      <div className="flex justify-center gap-0.5 mt-0.5">
        {hasEx && <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />}
        {hasDiet && <span className="w-1.5 h-1.5 rounded-full bg-orange-400" />}
      </div>
    );
  };

  const selectedDate = format(date, 'yyyy-MM-dd');
  const hasExOnDate = exerciseDates.has(selectedDate);
  const hasDietOnDate = dietDates.has(selectedDate);

  return (
    <div className="space-y-4">
      <div className="card">
        <div className="flex gap-4 text-xs text-gray-500 mb-4">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" /> 운동 기록</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-orange-400 inline-block" /> 식단 기록</span>
        </div>
        <Calendar
          onChange={(val: CalendarValue) => val instanceof Date && setDate(val)}
          value={date}
          tileContent={tileContent}
          locale="ko-KR"
          calendarType="gregory"
        />
      </div>

      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-3">{selectedDate} 기록</h3>
        {!hasExOnDate && !hasDietOnDate ? (
          <p className="text-sm text-gray-400">이 날의 기록이 없습니다.</p>
        ) : (
          <div className="space-y-2">
            {hasExOnDate && (
              <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                <Dumbbell className="w-4 h-4" /> 운동 기록 있음
              </div>
            )}
            {hasDietOnDate && (
              <div className="flex items-center gap-2 p-3 bg-orange-50 rounded-lg text-sm text-orange-700">
                <Utensils className="w-4 h-4" /> 식단 기록 있음
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
