import { Link } from 'react-router-dom';
import logoUrl from '../../assets/logo.png';

export default function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <Link to="/">
            <img src={logoUrl} alt="MOTI" className="h-24 w-auto" />
          </Link>
          <p className="text-sm text-gray-500">
            본 서비스의 건강 상담은 참고용이며, 의료 진단을 대체하지 않습니다.
          </p>
          <div className="flex gap-4 text-sm text-gray-500">
            <Link to="/board/health" className="hover:text-primary-600">건강정보</Link>
            <Link to="/board/exercise" className="hover:text-primary-600">운동정보</Link>
          </div>
        </div>
        <p className="text-center text-xs text-gray-400 mt-6">
          © 2025 MOTI. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
