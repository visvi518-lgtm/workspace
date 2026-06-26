import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Plus, Scale } from 'lucide-react';
import { healthApi } from '@/services/api';
import type { WeightRecord } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

export default function WeightTab() {
  const qc = useQueryClient();
  const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'));
  const [weight, setWeight] = useState('');

  const { data: records = [] } = useQuery<WeightRecord[]>({
    queryKey: ['weightRecords'],
    queryFn: () => healthApi.getWeightRecords().then((r) => r.data),
  });

  const addMutation = useMutation({
    mutationFn: () => healthApi.addWeightRecord({ date, weight: Number(weight) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['weightRecords'] });
      setWeight('');
      toast.success('체중이 기록되었습니다.');
    },
    onError: () => toast.error('기록에 실패했습니다.'),
  });

  const chartData = [...records]
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-30)
    .map((r) => ({ date: r.date.slice(5), weight: r.weight }));

  const latest = records[records.length - 1];
  const prev = records[records.length - 2];
  const diff = latest && prev ? (latest.weight - prev.weight).toFixed(1) : null;

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Scale className="w-5 h-5 text-primary-600" /> 체중 기록
        </h2>

        <div className="flex gap-3 mb-6">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="input-base flex-1"
          />
          <div className="relative flex-1">
            <input
              type="number"
              step="0.1"
              min="20"
              max="300"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="체중 (kg)"
              className="input-base pr-8"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-400">kg</span>
          </div>
          <button
            onClick={() => addMutation.mutate()}
            disabled={!weight || addMutation.isPending}
            className="btn-primary flex items-center gap-1 whitespace-nowrap"
          >
            <Plus className="w-4 h-4" /> 기록
          </button>
        </div>

        {latest && (
          <div className="flex gap-4 mb-6">
            <div className="flex-1 bg-primary-50 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-500 mb-1">현재 체중</p>
              <p className="text-3xl font-bold text-primary-700">{latest.weight}<span className="text-base font-normal">kg</span></p>
            </div>
            {diff !== null && (
              <div className="flex-1 bg-gray-50 rounded-xl p-4 text-center">
                <p className="text-xs text-gray-500 mb-1">전일 대비</p>
                <p className={`text-2xl font-bold ${Number(diff) > 0 ? 'text-red-500' : Number(diff) < 0 ? 'text-blue-500' : 'text-gray-500'}`}>
                  {Number(diff) > 0 ? '+' : ''}{diff}kg
                </p>
              </div>
            )}
          </div>
        )}

        {chartData.length > 1 && (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 11 }} unit="kg" />
                <Tooltip formatter={(v: number) => [`${v}kg`, '체중']} />
                <Line type="monotone" dataKey="weight" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="font-medium text-gray-900 mb-3">기록 내역</h3>
        <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
          {[...records].reverse().map((r) => (
            <div key={r.id} className="flex justify-between py-2.5 text-sm">
              <span className="text-gray-600">{r.date}</span>
              <span className="font-medium">{r.weight} kg</span>
            </div>
          ))}
          {records.length === 0 && (
            <p className="text-center text-gray-400 py-6 text-sm">체중을 기록해 보세요!</p>
          )}
        </div>
      </div>
    </div>
  );
}
