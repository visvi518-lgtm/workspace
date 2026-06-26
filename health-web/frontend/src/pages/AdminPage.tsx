import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Shield, Users, BarChart3, Ban, CheckCircle, Search } from 'lucide-react';
import { adminApi } from '@/services/api';
import type { User, BanDuration } from '@/types';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

const BAN_OPTIONS: { value: BanDuration; label: string }[] = [
  { value: '3d', label: '3일' },
  { value: '3w', label: '3주' },
  { value: '3m', label: '3개월' },
  { value: '3y', label: '3년' },
  { value: 'permanent', label: '영구정지' },
];

export default function AdminPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<'users' | 'stats'>('users');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [banModal, setBanModal] = useState<{ userId: number; nickname: string } | null>(null);
  const [banForm, setBanForm] = useState({ duration: '3d' as BanDuration, reason: '' });

  const { data } = useQuery({
    queryKey: ['adminUsers', page, search],
    queryFn: () => adminApi.getUsers({ page, search }).then((r) => r.data),
  });

  const { data: stats } = useQuery({
    queryKey: ['adminStats'],
    queryFn: () => adminApi.getStats().then((r) => r.data),
    enabled: tab === 'stats',
  });

  const banMutation = useMutation({
    mutationFn: () => adminApi.banUser({ user_id: banModal!.userId, ...banForm }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['adminUsers'] });
      setBanModal(null);
      setBanForm({ duration: '3d', reason: '' });
      toast.success('계정이 정지되었습니다.');
    },
  });

  const unbanMutation = useMutation({
    mutationFn: (userId: number) => adminApi.unbanUser(userId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['adminUsers'] });
      toast.success('계정 정지가 해제되었습니다.');
    },
  });

  const isBanned = (user: User) =>
    user.banned_until && new Date(user.banned_until) > new Date();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
        <Shield className="w-7 h-7 text-primary-600" /> 관리자 패널
      </h1>

      {/* Tabs */}
      <div className="flex gap-2">
        {[
          { id: 'users', label: '사용자 관리', Icon: Users },
          { id: 'stats', label: '통계', Icon: BarChart3 },
        ].map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id as 'users' | 'stats')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${tab === id ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {tab === 'users' && (
        <div className="card space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="이메일, 닉네임 검색"
              className="input-base pl-10"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                  <th className="pb-2 font-medium">닉네임</th>
                  <th className="pb-2 font-medium">이메일</th>
                  <th className="pb-2 font-medium">가입일</th>
                  <th className="pb-2 font-medium">상태</th>
                  <th className="pb-2 font-medium">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {(data?.items ?? []).map((user: User) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="py-3 font-medium">
                      {user.nickname}
                      {user.is_admin && (
                        <span className="ml-1 text-xs bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded">관리자</span>
                      )}
                    </td>
                    <td className="py-3 text-gray-500">{user.email}</td>
                    <td className="py-3 text-gray-500">{format(new Date(user.created_at), 'yyyy.MM.dd')}</td>
                    <td className="py-3">
                      {user.is_dormant ? (
                        <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">휴면</span>
                      ) : isBanned(user) ? (
                        <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                          정지 {user.banned_until && format(new Date(user.banned_until), '~MM.dd')}
                        </span>
                      ) : (
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">활성</span>
                      )}
                    </td>
                    <td className="py-3">
                      {!user.is_admin && (
                        isBanned(user) ? (
                          <button onClick={() => unbanMutation.mutate(user.id)} className="text-xs text-green-600 hover:underline flex items-center gap-1">
                            <CheckCircle className="w-3.5 h-3.5" /> 정지해제
                          </button>
                        ) : (
                          <button onClick={() => setBanModal({ userId: user.id, nickname: user.nickname })} className="text-xs text-red-500 hover:underline flex items-center gap-1">
                            <Ban className="w-3.5 h-3.5" /> 정지
                          </button>
                        )
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'stats' && stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: '전체 회원', value: stats.total_users },
            { label: '오늘 가입', value: stats.new_users_today },
            { label: '전체 게시글', value: stats.total_posts },
            { label: '정지 계정', value: stats.banned_users },
          ].map((s) => (
            <div key={s.label} className="card text-center">
              <p className="text-sm text-gray-500">{s.label}</p>
              <p className="text-3xl font-bold text-primary-600 mt-1">{s.value?.toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}

      {/* Ban modal */}
      {banModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl p-6 w-full max-w-md space-y-4">
            <h2 className="font-bold text-gray-900">{banModal.nickname} 계정 정지</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">정지 기간</label>
              <div className="flex flex-wrap gap-2">
                {BAN_OPTIONS.map((o) => (
                  <button
                    key={o.value}
                    onClick={() => setBanForm({ ...banForm, duration: o.value })}
                    className={`px-3 py-1.5 rounded-lg border text-sm transition-colors
                      ${banForm.duration === o.value ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 text-gray-600 hover:border-gray-300'}`}
                  >
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">정지 사유</label>
              <textarea
                rows={3}
                value={banForm.reason}
                onChange={(e) => setBanForm({ ...banForm, reason: e.target.value })}
                placeholder="정지 사유를 입력하세요"
                className="input-base resize-none"
              />
            </div>
            <div className="flex gap-3">
              <button onClick={() => setBanModal(null)} className="btn-secondary flex-1">취소</button>
              <button
                onClick={() => banMutation.mutate()}
                disabled={!banForm.reason.trim() || banMutation.isPending}
                className="btn-danger flex-1"
              >
                {banMutation.isPending ? '처리 중...' : '정지 적용'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
