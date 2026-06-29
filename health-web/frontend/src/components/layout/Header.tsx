import { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { Menu, X, Heart, ChevronDown, User, LogOut, Settings, Shield } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropOpen, setDropOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
    setDropOpen(false);
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 text-primary-600 font-bold text-xl">
            <Heart className="w-6 h-6 fill-current" />
            헬스케어
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {isAuthenticated && (
              <>
                <NavLink
                  to="/health"
                  className={({ isActive }) =>
                    `font-medium ${isActive ? 'text-primary-600' : 'text-gray-700 hover:text-primary-600'}`
                  }
                >
                  건강관리
                </NavLink>
                <NavLink
                  to="/chat"
                  className={({ isActive }) =>
                    `font-medium ${isActive ? 'text-primary-600' : 'text-gray-700 hover:text-primary-600'}`
                  }
                >
                  건강상담
                </NavLink>
              </>
            )}
            <NavLink
              to="/board/health"
              className={({ isActive }) =>
                `font-medium ${isActive ? 'text-primary-600' : 'text-gray-700 hover:text-primary-600'}`
              }
            >
              건강정보
            </NavLink>
            <NavLink
              to="/board/exercise"
              className={({ isActive }) =>
                `font-medium ${isActive ? 'text-primary-600' : 'text-gray-700 hover:text-primary-600'}`
              }
            >
              운동정보
            </NavLink>
            {isAuthenticated && (
              <NavLink
                to="/free-board"
                className={({ isActive }) =>
                  `font-medium ${isActive ? 'text-primary-600' : 'text-gray-700 hover:text-primary-600'}`
                }
              >
                자유게시판
              </NavLink>
            )}
          </nav>

          {/* Auth */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="relative">
                <button
                  onClick={() => setDropOpen(!dropOpen)}
                  className="flex items-center gap-2 text-gray-700 hover:text-primary-600"
                >
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                    <User className="w-4 h-4 text-primary-600" />
                  </div>
                  <span className="font-medium text-sm">{user?.nickname}</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
                {dropOpen && (
                  <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border
                                  border-gray-100 py-1 z-50">
                    <Link
                      to="/my-page"
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      onClick={() => setDropOpen(false)}
                    >
                      <Settings className="w-4 h-4" /> 마이페이지
                    </Link>
                    {user?.is_admin && (
                      <Link
                        to="/admin"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-primary-600 hover:bg-primary-50"
                        onClick={() => setDropOpen(false)}
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
                )}
              </div>
            ) : (
              <>
                <Link to="/login" className="btn-secondary text-sm">로그인</Link>
                <Link to="/register" className="btn-primary text-sm">회원가입</Link>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 text-gray-600"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white py-3 px-4 space-y-1">
          {isAuthenticated && (
            <>
              <NavLink to="/health" className="block py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50" onClick={() => setMenuOpen(false)}>건강관리</NavLink>
              <NavLink to="/chat" className="block py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50" onClick={() => setMenuOpen(false)}>건강상담</NavLink>
            </>
          )}
          <NavLink to="/board/health" className="block py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50" onClick={() => setMenuOpen(false)}>건강정보</NavLink>
          <NavLink to="/board/exercise" className="block py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50" onClick={() => setMenuOpen(false)}>운동정보</NavLink>
          {isAuthenticated && (
            <>
              <NavLink to="/free-board" className="block py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50" onClick={() => setMenuOpen(false)}>자유게시판</NavLink>
              <NavLink to="/my-page" className="block py-2 px-3 rounded-lg text-gray-700 hover:bg-gray-50" onClick={() => setMenuOpen(false)}>마이페이지</NavLink>
              {user?.is_admin && (
                <NavLink to="/admin" className="block py-2 px-3 rounded-lg text-primary-600 hover:bg-primary-50" onClick={() => setMenuOpen(false)}>관리자</NavLink>
              )}
              <button onClick={handleLogout} className="block w-full text-left py-2 px-3 rounded-lg text-red-600 hover:bg-red-50">로그아웃</button>
            </>
          )}
          {!isAuthenticated && (
            <div className="flex gap-2 pt-2">
              <Link to="/login" className="btn-secondary flex-1 text-center text-sm" onClick={() => setMenuOpen(false)}>로그인</Link>
              <Link to="/register" className="btn-primary flex-1 text-center text-sm" onClick={() => setMenuOpen(false)}>회원가입</Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
