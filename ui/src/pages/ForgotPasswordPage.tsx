import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Loader2, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authService } from '@/services/authService';

export default function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      await authService.sendCode(email);
      setStep(2);
      alert('验证码已发送至您的邮箱！');
    } catch (err: any) {
      console.error('Send code failed:', err);
      setError(err.response?.data?.detail || '发送验证码失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation only, as API verifies code during reset
    if (code.length !== 6 || !/^\d+$/.test(code)) {
      setError('请输入有效的6位数字验证码');
      return;
    }
    setStep(3);
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('两次输入的密码不一致');
      setIsLoading(false);
      return;
    }

    if (newPassword.length < 6) {
      setError('密码长度至少为6位');
      setIsLoading(false);
      return;
    }

    try {
      await authService.resetPassword({
        email,
        code,
        new_password: newPassword
      });
      
      alert('密码重置成功！请使用新密码登录。');
      navigate('/login');
    } catch (err: any) {
      console.error('Reset password failed:', err);
      setError(err.response?.data?.detail || '重置密码失败');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-black font-sans text-white">
      {/* Background Image with Overlay */}
      <div 
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat opacity-60"
        style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?q=80&w=2070&auto=format&fit=crop")' }}
      />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-black/30 via-black/60 to-black/90" />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 py-12">
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="w-full max-w-sm"
        >
          <Button 
            variant="ghost" 
            className="mb-8 pl-0 text-white/70 hover:text-white hover:bg-transparent"
            onClick={() => navigate('/login')}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            返回登录
          </Button>

          <div className="mb-8">
            <h1 className="font-serif text-3xl font-light tracking-tight text-white">
              {step === 1 && "重置密码"}
              {step === 2 && "验证验证码"}
              {step === 3 && "设置新密码"}
            </h1>
            <p className="mt-2 text-white/60">
              {step === 1 && "输入您的邮箱以接收验证码。"}
              {step === 2 && `请输入发送至 ${email} 的6位验证码`}
              {step === 3 && "为您的账号创建新密码。"}
            </p>
          </div>

          <div className="space-y-6">
            {step === 1 && (
              <form onSubmit={handleSendCode} className="space-y-4">
                <Input
                  type="email"
                  placeholder="邮箱地址"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
                />
                <Button 
                  type="submit" 
                  className="w-full bg-white text-black hover:bg-white/90 h-12"
                  disabled={isLoading}
                >
                  {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : '发送验证码'}
                </Button>
              </form>
            )}

            {step === 2 && (
              <form onSubmit={handleVerifyCode} className="space-y-4">
                <Input
                  type="text"
                  placeholder="验证码 (6位数字)"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  required
                  maxLength={6}
                  className="bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10 text-center tracking-widest text-lg"
                />
                <Button 
                  type="submit" 
                  className="w-full bg-white text-black hover:bg-white/90 h-12"
                >
                  下一步
                </Button>
              </form>
            )}

            {step === 3 && (
              <form onSubmit={handleResetPassword} className="space-y-4">
                <Input
                  type="password"
                  placeholder="新密码"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
                />
                <Input
                  type="password"
                  placeholder="确认新密码"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-white/30 focus:bg-white/10"
                />
                <Button 
                  type="submit" 
                  className="w-full bg-white text-black hover:bg-white/90 h-12"
                  disabled={isLoading}
                >
                  {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : '重置密码'}
                </Button>
              </form>
            )}

            {error && (
              <div className="rounded-md bg-red-500/10 p-3 text-sm text-red-200 border border-red-500/20 text-center">
                {error}
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
