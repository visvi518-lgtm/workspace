import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Shield, Users, BarChart3, Ban, CheckCircle, Search,
  Database, RefreshCw, CheckSquare, XSquare, ExternalLink,
  Heart, Dumbbell, Tag, StopCircle,
  Image as ImageIcon, Trash2, Eye, EyeOff, Plus, Salad,
} from 'lucide-react';
import { adminApi } from '@/services/api';
import RecommendationAdmin from '@/components/admin/RecommendationAdmin';

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1';
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

type MainTab = 'users' | 'content' | 'stats' | 'banner' | 'recommendation';
type ContentBoard = 'health' | 'exercise';
type ContentStatus = 'draft' | 'published' | 'rejected';

const STATUS_LABEL: Record<ContentStatus, string> = {
  draft: '검토중',
  published: '게시됨',
  rejected: '거절됨',
};
const STATUS_COLOR: Record<ContentStatus, string> = {
  draft: 'bg-yellow-100 text-yellow-700',
  published: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
};

export default function AdminPage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<MainTab>('users');

  // ─── Users tab state ───
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [banModal, setBanModal] = useState<{ userId: number; nickname: string } | null>(null);
  const [banForm, setBanForm] = useState({ duration: '3d' as BanDuration, reason: '' });

  // ─── Banner tab state ───
  const [addingBanner, setAddingBanner] = useState(false);
  const [bannerTitle, setBannerTitle] = useState('');
  const [bannerSubtitle, setBannerSubtitle] = useState('');
  const [bannerLinkUrl, setBannerLinkUrl] = useState('');
  const [bannerImage, setBannerImage] = useState<File | null>(null);
  const [bannerPreview, setBannerPreview] = useState<string | null>(null);

  // ─── Content tab state ───
  const [contentBoard, setContentBoard] = useState<ContentBoard>('health');
  const [contentStatus, setContentStatus] = useState<ContentStatus>('draft');

  // ─── Queries ───
  const { data: adminBanners = [] } = useQuery<any[]>({
    queryKey: ['adminBanners'],
    queryFn: () => adminApi.getAdminBanners().then((r) => r.data),
    enabled: tab === 'banner',
  });

  const { data: userData } = useQuery({
    queryKey: ['adminUsers', page, search],
    queryFn: () => adminApi.getUsers({ page, search }).then((r) => r.data),
    enabled: tab === 'users',
  });

  const { data: stats } = useQuery({
    queryKey: ['adminStats'],
    queryFn: () => adminApi.getStats().then((r) => r.data),
    enabled: tab === 'stats',
  });

  const { data: contentData, refetch: refetchContent, isFetching: contentFetching } = useQuery({
    queryKey: ['adminContent', contentBoard, contentStatus],
    queryFn: () =>
      adminApi.getContent({ board_type: contentBoard, crawl_status: contentStatus }).then((r) => r.data),
    enabled: tab === 'content',
  });

  // 크롤링 실행 상태 폴링 (크롤링 중일 때만 3초마다)
  const { data: crawlStatus } = useQuery({
    queryKey: ['crawlStatus'],
    queryFn: () => adminApi.getCrawlStatus().then((r) => r.data),
    enabled: tab === 'content',
    refetchInterval: (data) => (data?.state.data?.running ? 3000 : false),
  });
  const isCrawlingNow = crawlStatus?.running ?? false;

  // ─── Mutations ───
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

  const publishMutation = useMutation({
    mutationFn: (id: number) => adminApi.publishContent(id),
    onSuccess: () => { refetchContent(); toast.success('게시되었습니다.'); },
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => adminApi.rejectContent(id),
    onSuccess: () => { refetchContent(); toast.success('거절되었습니다.'); },
  });

  const seedMutation = useMutation({
    mutationFn: () => adminApi.seedContent(),
    onSuccess: (res) => {
      refetchContent();
      toast.success(res.data.total > 0 ? `샘플 데이터 ${res.data.total}개 추가됨` : '이미 샘플 데이터가 있습니다.');
    },
  });

  const crawlMutation = useMutation({
    mutationFn: () => adminApi.triggerCrawl(contentBoard),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ['crawlStatus'] });
      refetchContent();
      if (res.data.stopped) {
        toast('크롤링이 중단되어 데이터가 저장되지 않았습니다.', { icon: '⚠️' });
      } else {
        toast.success(
          `크롤링 완료 — ${res.data.saved}개 저장 / 중복 ${(res.data.skipped_url ?? 0) + (res.data.skipped_dup ?? 0)}개 제외`
        );
      }
    },
    onError: (err: any) => {
      qc.invalidateQueries({ queryKey: ['crawlStatus'] });
      toast.error(err.response?.data?.detail || '크롤링에 실패했습니다.');
    },
  });

  const createBannerMutation = useMutation({
    mutationFn: () => {
      const fd = new FormData();
      if (bannerTitle) fd.append('title', bannerTitle);
      if (bannerSubtitle) fd.append('subtitle', bannerSubtitle);
      if (bannerLinkUrl) fd.append('link_url', bannerLinkUrl);
      if (bannerImage) fd.append('image', bannerImage);
      return adminApi.createBanner(fd);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['adminBanners'] });
      qc.invalidateQueries({ queryKey: ['banners'] });
      setBannerTitle(''); setBannerSubtitle(''); setBannerLinkUrl('');
      setBannerImage(null); setBannerPreview(null);
      setAddingBanner(false);
      toast.success('배너가 추가되었습니다.');
    },
    onError: (err: any) => toast.error(err.response?.data?.detail || '추가에 실패했습니다.'),
  });

  const deleteBannerMutation = useMutation({
    mutationFn: (id: number) => adminApi.deleteBanner(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['adminBanners'] });
      qc.invalidateQueries({ queryKey: ['banners'] });
      toast.success('배너가 삭제되었습니다.');
    },
  });

  const toggleBannerMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      adminApi.toggleBanner(id, is_active),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['adminBanners'] });
      qc.invalidateQueries({ queryKey: ['banners'] });
    },
  });

  const stopCrawlMutation = useMutation({
    mutationFn: () => adminApi.stopCrawl(),
    onSuccess: () => {
      toast('크롤링 중단 요청됨 — 수집 데이터가 폐기됩니다.', { icon: '⏹' });
    },
  });

  const isBanned = (user: User) =>
    user.banned_until && new Date(user.banned_until) > new Date();

  const TABS: { id: MainTab; label: string; Icon: React.ComponentType<any> }[] = [
    { id: 'users', label: '사용자 관리', Icon: Users },
    { id: 'content', label: '데이터 관리', Icon: Database },
    { id: 'stats', label: '통계', Icon: BarChart3 },
    { id: 'banner', label: '배너 관리', Icon: ImageIcon },
    { id: 'recommendation', label: '추천 관리', Icon: Salad },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
        <Shield className="w-7 h-7 text-primary-600" /> 관리자 패널
      </h1>

      {/* Main Tabs */}
      <div className="flex gap-2">
        {TABS.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${tab === id ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
          >
            <Icon className="w-4 h-4" /> {label}
          </button>
        ))}
      </div>

      {/* ─── Users Tab ─── */}
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
                {(userData?.items ?? []).map((user: User) => (
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

      {/* ─── Content Tab ─── */}
      {tab === 'content' && (
        <div className="space-y-4">
          {/* Board type + action buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex gap-1">
              {([
                { id: 'health', label: '건강정보', Icon: Heart },
                { id: 'exercise', label: '운동정보', Icon: Dumbbell },
              ] as const).map(({ id, label, Icon }) => (
                <button
                  key={id}
                  onClick={() => setContentBoard(id)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                    ${contentBoard === id ? 'bg-primary-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
                >
                  <Icon className="w-4 h-4" /> {label}
                </button>
              ))}
            </div>

            <div className="ml-auto flex gap-2">
              <button
                onClick={() => seedMutation.mutate()}
                disabled={seedMutation.isPending}
                className="btn-secondary text-sm flex items-center gap-1.5"
              >
                <Database className="w-4 h-4" />
                {seedMutation.isPending ? '추가 중...' : '샘플 데이터'}
              </button>
              {isCrawlingNow || crawlMutation.isPending ? (
                <button
                  onClick={() => stopCrawlMutation.mutate()}
                  disabled={stopCrawlMutation.isPending}
                  className="text-sm flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors"
                >
                  <StopCircle className="w-4 h-4" />
                  수집 중단
                </button>
              ) : (
                <button
                  onClick={() => crawlMutation.mutate()}
                  disabled={crawlMutation.isPending}
                  className="btn-primary text-sm flex items-center gap-1.5"
                >
                  <RefreshCw className="w-4 h-4" />
                  크롤링 실행
                </button>
              )}
            </div>
          </div>

          {/* Status filter */}
          <div className="flex gap-1">
            {(['draft', 'published', 'rejected'] as ContentStatus[]).map((s) => (
              <button
                key={s}
                onClick={() => setContentStatus(s)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                  ${contentStatus === s ? STATUS_COLOR[s] + ' border border-current/20' : 'bg-white text-gray-500 border border-gray-200 hover:bg-gray-50'}`}
              >
                {STATUS_LABEL[s]}
                {contentData && contentStatus === s && (
                  <span className="ml-1.5 text-xs opacity-70">({contentData.total})</span>
                )}
              </button>
            ))}
          </div>

          {/* Content list */}
          <div className="space-y-3">
            {contentFetching && (
              <div className="text-center py-8 text-gray-400 text-sm">불러오는 중...</div>
            )}
            {!contentFetching && (contentData?.items ?? []).length === 0 && (
              <div className="card text-center py-10 text-gray-400">
                <Database className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-sm">
                  {contentStatus === 'draft' ? '검토할 게시물이 없습니다.' : `${STATUS_LABEL[contentStatus]} 게시물이 없습니다.`}
                </p>
                {contentStatus === 'draft' && (
                  <p className="text-xs mt-1 text-gray-300">
                    "샘플 데이터" 버튼으로 테스트 데이터를 추가하거나 크롤링을 실행하세요.
                  </p>
                )}
              </div>
            )}

            {(contentData?.items ?? []).map((post: any) => (
              <div key={post.id} className="card border border-gray-100 hover:border-gray-200 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[post.crawl_status as ContentStatus]}`}>
                        {STATUS_LABEL[post.crawl_status as ContentStatus]}
                      </span>
                      <span className="text-xs text-gray-400">
                        {format(new Date(post.created_at), 'yyyy.MM.dd')}
                      </span>
                    </div>
                    <h3 className="font-medium text-gray-900 text-sm leading-snug mb-1 line-clamp-2">
                      {post.title}
                    </h3>
                    {post.summary && (
                      <p className="text-xs text-gray-500 line-clamp-2 mb-2">{post.summary}</p>
                    )}
                    <div className="flex flex-wrap gap-1">
                      {(post.tags ?? []).map((tag: string) => (
                        <span key={tag} className="inline-flex items-center gap-0.5 text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                          <Tag className="w-2.5 h-2.5" /> {tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex flex-col gap-1 shrink-0">
                    {post.source_url && (
                      <a
                        href={post.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-gray-400 hover:text-primary-600 flex items-center gap-0.5"
                      >
                        <ExternalLink className="w-3 h-3" /> 원문
                      </a>
                    )}
                    {post.crawl_status !== 'published' && (
                      <button
                        onClick={() => publishMutation.mutate(post.id)}
                        disabled={publishMutation.isPending}
                        className="flex items-center gap-1 text-xs bg-green-50 text-green-700 hover:bg-green-100 px-2 py-1 rounded-lg font-medium transition-colors"
                      >
                        <CheckSquare className="w-3.5 h-3.5" /> 게시
                      </button>
                    )}
                    {post.crawl_status !== 'rejected' && (
                      <button
                        onClick={() => rejectMutation.mutate(post.id)}
                        disabled={rejectMutation.isPending}
                        className="flex items-center gap-1 text-xs bg-red-50 text-red-600 hover:bg-red-100 px-2 py-1 rounded-lg font-medium transition-colors"
                      >
                        <XSquare className="w-3.5 h-3.5" /> 거절
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Stats Tab ─── */}
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

      {/* ─── Banner Tab ─── */}
      {tab === 'banner' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              최대 4개 등록 가능 · 3초 간격 우→좌 슬라이드
            </p>
            {adminBanners.length < 4 && !addingBanner && (
              <button
                onClick={() => setAddingBanner(true)}
                className="btn-primary text-sm flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" /> 새 배너 추가
              </button>
            )}
          </div>

          {/* 추가 폼 */}
          {addingBanner && (
            <div className="card border border-primary-100 space-y-4">
              <h3 className="font-semibold text-gray-900 text-sm">새 배너</h3>

              {/* 이미지 업로드 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">이미지</label>
                <label className="block cursor-pointer">
                  {bannerPreview ? (
                    <div className="relative rounded-xl overflow-hidden h-36">
                      <img src={bannerPreview} alt="preview" className="w-full h-full object-cover" />
                      <div className="absolute inset-0 bg-black/30 flex items-center justify-center text-white text-xs">
                        클릭하여 변경
                      </div>
                    </div>
                  ) : (
                    <div className="h-36 border-2 border-dashed border-gray-200 rounded-xl flex flex-col items-center justify-center text-gray-400 hover:border-primary-300 hover:text-primary-400 transition-colors">
                      <ImageIcon className="w-8 h-8 mb-2" />
                      <span className="text-sm">이미지 선택 (최대 5MB)</span>
                    </div>
                  )}
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        setBannerImage(file);
                        setBannerPreview(URL.createObjectURL(file));
                      }
                    }}
                  />
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">제목</label>
                <input
                  type="text"
                  value={bannerTitle}
                  onChange={(e) => setBannerTitle(e.target.value)}
                  placeholder="배너 제목 (선택)"
                  className="input-base"
                  maxLength={100}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">부제목</label>
                <input
                  type="text"
                  value={bannerSubtitle}
                  onChange={(e) => setBannerSubtitle(e.target.value)}
                  placeholder="배너 부제목 (선택)"
                  className="input-base"
                  maxLength={200}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">링크 URL</label>
                <input
                  type="url"
                  value={bannerLinkUrl}
                  onChange={(e) => setBannerLinkUrl(e.target.value)}
                  placeholder="https://example.com (클릭 시 이동, 선택)"
                  className="input-base"
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setAddingBanner(false);
                    setBannerTitle(''); setBannerSubtitle(''); setBannerLinkUrl('');
                    setBannerImage(null); setBannerPreview(null);
                  }}
                  className="btn-secondary flex-1"
                >
                  취소
                </button>
                <button
                  onClick={() => createBannerMutation.mutate()}
                  disabled={createBannerMutation.isPending || (!bannerImage && !bannerTitle)}
                  className="btn-primary flex-1"
                >
                  {createBannerMutation.isPending ? '저장 중...' : '저장'}
                </button>
              </div>
            </div>
          )}

          {/* 배너 목록 */}
          {adminBanners.length === 0 && !addingBanner ? (
            <div className="card text-center py-12 text-gray-400">
              <ImageIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
              <p className="text-sm">등록된 배너가 없습니다.</p>
              <p className="text-xs mt-1 text-gray-300">위 버튼으로 배너를 추가하세요.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {adminBanners.map((banner: any) => (
                <div key={banner.id} className="card border border-gray-100 flex items-center gap-4">
                  {/* 썸네일 */}
                  <div className="w-24 h-16 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                    {banner.has_image ? (
                      <img
                        src={`${API_BASE}/banners/${banner.id}/image`}
                        alt={banner.title ?? '배너'}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-primary-200 to-primary-100 flex items-center justify-center">
                        <ImageIcon className="w-5 h-5 text-primary-400" />
                      </div>
                    )}
                  </div>

                  {/* 텍스트 */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-gray-900 truncate">
                      {banner.title || <span className="text-gray-400">제목 없음</span>}
                    </p>
                    {banner.subtitle && (
                      <p className="text-xs text-gray-500 truncate mt-0.5">{banner.subtitle}</p>
                    )}
                    {banner.link_url && (
                      <a
                        href={banner.link_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary-500 hover:underline truncate mt-0.5 flex items-center gap-1"
                      >
                        <ExternalLink className="w-3 h-3 flex-shrink-0" />
                        {banner.link_url}
                      </a>
                    )}
                    <p className="text-xs text-gray-400 mt-1">순서 {banner.order_idx + 1}</p>
                  </div>

                  {/* 액션 */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => toggleBannerMutation.mutate({ id: banner.id, is_active: !banner.is_active })}
                      className={`flex items-center gap-1 text-xs px-2 py-1.5 rounded-lg font-medium transition-colors ${
                        banner.is_active
                          ? 'bg-green-50 text-green-700 hover:bg-green-100'
                          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                      }`}
                    >
                      {banner.is_active ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                      {banner.is_active ? '활성' : '숨김'}
                    </button>
                    <button
                      onClick={() => deleteBannerMutation.mutate(banner.id)}
                      disabled={deleteBannerMutation.isPending}
                      className="flex items-center gap-1 text-xs px-2 py-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 font-medium transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> 삭제
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── Recommendation Tab ─── */}
      {tab === 'recommendation' && <RecommendationAdmin />}

      {/* ─── Ban Modal ─── */}
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
