import { useState } from 'react';
import logoUrl from '../../assets/logo.png';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import {
  Menu, X, User, LogOut, Settings, Shield,
  Activity, MessageCircle, Newspaper, Dumbbell, MessageSquare, ChevronRight,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

const NAV_ITEMS = [
  { to: '/health',         label: '운동 및 식단 기록', Icon: Activity,       authRequired: true  },
  { to: '/chat',           label: 'AI 상담',           Icon: MessageCircle,  authRequired: true  },
  { to: '/board/health',   label: '건강정보',           Icon: Newspaper,      authRequired: false },
  { to: '/board/exercise', label: '운동정보',           Icon: Dumbbell,       authRequired: false },
  { to: '/free-board',     label: '자유게시판',         Icon: MessageSquare,  authRequired: true  },
];

export default function Header() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userDropOpen, setUserDropOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
    setUserDropOpen(false);
    setSidebarOpen(false);
  };

  const visibleItems = NAV_ITEMS.filter((item) => !item.authRequired || isAuthenticated);

  return (
    <>
      {/* ─── Header bar ─── */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">

            {/* Left: hamburger + logo */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
                aria-label="메뉴 열기"
              >
                <Menu className="w-5 h-5" />
              </button>
              <Link to="/">
                <img src={logoUrl} alt="MOTI" className="h-28 w-auto" />
              </Link>
            </div>

            {/* Right: auth */}
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <div className="relative">
                  <button
                    onClick={() => setUserDropOpen(!userDropOpen)}
                    className="flex items-center gap-2 text-gray-700 hover:text-primary-600"
                  >
                    <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                      <User className="w-4 h-4 text-primary-600" />
                    </div>
                    <span className="hidden sm:block font-medium text-sm">{user?.nickname}</span>
                  </button>
                  {userDropOpen && (
                    <>
                      {/* backdrop */}
                      <div className="fixed inset-0 z-40" onClick={() => setUserDropOpen(false)} />
                      <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border
                                      border-gray-100 py-1 z-50">
                        <Link
                          to="/my-page"
                          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                          onClick={() => setUserDropOpen(false)}
                        >
                          <Settings className="w-4 h-4" /> 마이페이지
                        </Link>
                        {user?.is_admin && (
                          <Link
                            to="/admin"
                            className="flex items-center gap-2 px-4 py-2 text-sm text-primary-600 hover:bg-primary-50"
                            onClick={() => setUserDropOpen(false)}
                          >
                            <Shield className="w-4 h-4" /> 관리자
                          </Link>
                        )}
                        <hr className="my-1 border-gray-100" />
                        <button
                          onClick={handleLogout}
                          className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full"
                        >
                          <LogOut className="w-4 h-4" /> 로그아웃
                        </button>
                      </div>
                    </>
                  )}
                </div>
              ) : (
                <>
                  <Link to="/login" className="btn-secondary text-sm">로그인</Link>
                  <Link to="/register" className="btn-primary text-sm">회원가입</Link>
                </>
              )}
            </div>

          </div>
        </div>
      </header>

      {/* ─── Sidebar backdrop ─── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ─── Sidebar drawer ─── */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white shadow-2xl z-50
                    flex flex-col transition-transform duration-300 ease-in-out
                    ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between px-5 h-16 border-b border-gray-100">
          <Link to="/" onClick={() => setSidebarOpen(false)}>
            <img src={logoUrl} alt="MOTI" className="h-24 w-auto" />
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          <ul className="space-y-1">
            {visibleItems.map(({ to, label, Icon }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors
                     ${isActive
                       ? 'bg-primary-50 text-primary-700'
                       : 'text-gray-700 hover:bg-gray-50 hover:text-primary-600'
                     }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
                      <span className="flex-1">{label}</span>
                      {isActive && <ChevronRight className="w-4 h-4 text-primary-400" />}
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        {/* Sidebar footer (로그인 상태) */}
        {isAuthenticated ? (
          <div className="border-t border-gray-100 p-4 space-y-1">
            <Link
              to="/my-page"
              onClick={() => setSidebarOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-gray-700 hover:bg-gray-50"
            >
              <Settings className="w-4 h-4 text-gray-400" />
              마이페이지
            </Link>
            {user?.is_admin && (
              <Link
                to="/admin"
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-primary-600 hover:bg-primary-50"
              >
                <Shield className="w-4 h-4" />
                관리자
              </Link>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-red-600 hover:bg-red-50 w-full"
            >
              <LogOut className="w-4 h-4" />
              로그아웃
            </button>
          </div>
        ) : (
          <div className="border-t border-gray-100 p-4 flex flex-col gap-2">
            <Link
              to="/login"
              onClick={() => setSidebarOpen(false)}
              className="btn-secondary text-sm text-center"
            >
              로그인
            </Link>
            <Link
              to="/register"
              onClick={() => setSidebarOpen(false)}
              className="btn-primary text-sm text-center"
            >
              회원가입
            </Link>
          </div>
        )}
      </aside>
    </>
  );
}
