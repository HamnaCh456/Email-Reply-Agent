import React from 'react';

interface InboxItemProps {
   sender: string;
   subject: string;
   preview: string;
   isActive: boolean;
   onClick: () => void;
}

export const InboxItem: React.FC<InboxItemProps> = ({ sender, subject, preview, isActive, onClick }) => {
   return (
      <div
         onClick={onClick}
         className={`
        group relative p-6 cursor-pointer transition-all duration-300 ease-out border-b border-gray-50
        ${isActive
               ? 'bg-white shadow-[inset_3px_0_0_black] z-10'
               : 'hover:bg-gray-50'
            }
      `}
      >
         {/* Active Indicator */}
         {isActive && (
            <div className="absolute left-0 top-4 bottom-4 w-1 bg-black rounded-r-full" />
         )}

         <div className="flex flex-col gap-1">
            <div className="flex justify-between items-center">
               <span className={`text-xs font-bold tracking-wider uppercase ${isActive ? 'text-black' : 'text-gray-500'}`}>
                  {sender}
               </span>
               <span className="text-[10px] text-gray-400 font-medium">10:42 AM</span>
            </div>

            <h3 className={`font-display text-[17px] font-semibold leading-snug ${isActive ? 'text-black' : 'text-gray-800'}`}>
               {subject}
            </h3>

            <p className={`text-sm leading-relaxed line-clamp-2 ${isActive ? 'text-gray-600' : 'text-gray-400'}`}>
               {preview}
            </p>
         </div>
      </div>
   );
};
