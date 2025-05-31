import type { ReactNode } from 'react';
import { X } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SidePanelLayoutProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  width?: 'sm' | 'md' | 'lg' | 'xl';
  children: ReactNode;
  showCloseButton?: boolean;
  preventBackgroundClose?: boolean;
  className?: string;
}

const widthClasses = {
  sm: 'sm:max-w-sm',
  md: 'sm:max-w-md',
  lg: 'sm:max-w-lg',
  xl: 'sm:max-w-xl',
};

export function SidePanelLayout({
  isOpen,
  onClose,
  title,
  description,
  width = 'lg',
  children,
  showCloseButton = true,
  preventBackgroundClose = false,
  className = '',
}: SidePanelLayoutProps) {
  return (
    <Sheet 
      open={isOpen} 
      onOpenChange={(open) => {
        if (!open && !preventBackgroundClose) {
          onClose();
        }
      }}
    >
      <SheetContent 
        side="right"
        className={`${widthClasses[width]} w-full ${className}`}
        onInteractOutside={(e) => {
          if (preventBackgroundClose) {
            e.preventDefault();
          }
        }}
      >
        <SheetHeader className="space-y-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1 flex-1">
              <SheetTitle className="text-lg font-semibold text-gray-900">
                {title}
              </SheetTitle>
              {description && (
                <SheetDescription className="text-sm text-gray-600">
                  {description}
                </SheetDescription>
              )}
            </div>
          </div>
        </SheetHeader>
        
        <ScrollArea className="h-[calc(100vh-140px)] pr-4">
          <div className="space-y-6 py-4">
            {children}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

// Alternative drawer-based implementation for different use cases
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';

interface SidePanelDrawerProps extends Omit<SidePanelLayoutProps, 'width'> {
  direction?: 'left' | 'right' | 'top' | 'bottom';
}

export function SidePanelDrawer({
  isOpen,
  onClose,
  title,
  description,
  direction = 'right',
  children,
  showCloseButton = true,
  preventBackgroundClose = false,
  className = '',
}: SidePanelDrawerProps) {
  return (
    <Drawer 
      open={isOpen} 
      onOpenChange={(open) => {
        if (!open && !preventBackgroundClose) {
          onClose();
        }
      }}
      direction={direction}
    >
      <DrawerContent className={`${className}`}>
        <div className="mx-auto w-full max-w-4xl">
          <DrawerHeader className="text-left">
            <div className="flex items-start justify-between">
              <div className="space-y-1 flex-1">
                <DrawerTitle className="text-lg font-semibold text-gray-900">
                  {title}
                </DrawerTitle>
                {description && (
                  <DrawerDescription className="text-sm text-gray-600">
                    {description}
                  </DrawerDescription>
                )}
              </div>
              {showCloseButton && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-6 w-6 p-0 hover:bg-gray-100"
                  aria-label="Close"
                  autoFocus
                >
                  <X className="h-4 w-4" />
                  <span className="sr-only">Close panel</span>
                </Button>
              )}
            </div>
          </DrawerHeader>
          
          <div className="p-4 pb-8">
            <ScrollArea className="h-[60vh]">
              <div className="space-y-6">
                {children}
              </div>
            </ScrollArea>
          </div>
        </div>
      </DrawerContent>
    </Drawer>
  );
} 