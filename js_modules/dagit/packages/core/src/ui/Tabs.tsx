import React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from './Colors';
import {IconWrapper} from './Icon';
import {FontFamily} from './styles';

interface TabsProps {
  children: Array<React.ReactElement<TabProps>>;
  selectedTabId?: string;
  onChange?: (selectedTabId: string) => void;
  small?: boolean;
}

export const Tabs = styled(({selectedTabId, children, small, onChange, ...rest}) => {
  if (!(children instanceof Array) || children.some((c) => c.type !== Tab)) {
    throw new Error('Tabs must render Tab instances');
  }

  return (
    <div {...rest} role="tablist">
      {children.map((child) =>
        React.cloneElement(child, {
          key: child.props.key || child.props.id,
          selected: child.props.selected || child.props.id === selectedTabId,
          $small: small,
          ...(onChange && !child.props.disabled
            ? {
                onClick: () => onChange(child.props.id),
                onKeyDown: (e: React.KeyboardEvent) =>
                  [' ', 'Return', 'Enter'].includes(e.key) && onChange(child.props.id),
              }
            : {}),
        }),
      )}
    </div>
  );
})<TabsProps>`
  display: flex;
  gap: 16px;
  border-bottom: 1px solid ${ColorsWIP.Gray100};
  font-size: ${({small}) => (small ? '12px' : '14px')};
  line-height: ${({small}) => (small ? '16px' : '20px')};
  font-weight: 600;
`;

interface TabProps {
  id: string;
  title: React.ReactNode;
  disabled?: boolean;
  selected?: boolean;
  count?: number;
  icon: React.ReactNode;
  $small?: boolean;
}

export const Tab = styled(({title, count, icon, selected, disabled, ...rest}) => (
  <div
    role="tab"
    tabIndex={disabled ? -1 : 0}
    aria-disabled={disabled}
    aria-expanded={selected}
    aria-selected={selected}
    {...rest}
  >
    {title}
    {icon}
    {count && <Count>{count}</Count>}
  </div>
))<TabProps>`
  padding: ${({$small}) => ($small ? '12px 0 10px' : '18px 0 16px')};
  border-bottom: ${({selected}) => (selected ? ColorsWIP.Blue500 : 'transparent')} solid 2px;
  display: flex;
  align-items: center;
  gap: 6px;

  &,
  & a {
    cursor: default;
    user-select: none;
    color: ${({selected, disabled}) =>
      selected ? ColorsWIP.Blue500 : disabled ? ColorsWIP.Gray300 : ColorsWIP.Gray700};
  }

  & ${IconWrapper} {
    color: ${({selected, disabled}) =>
      selected ? ColorsWIP.Blue500 : disabled ? ColorsWIP.Gray300 : ''};
  }

  /* Focus outline only when using keyboard, not when focusing via mouse. */
  &:focus {
    outline: none !important;
    border-bottom: ${({selected}) => (selected ? ColorsWIP.Blue500 : ColorsWIP.Blue200)} solid 2px;
  }

  &:hover {
    &,
    a {
      text-decoration: none;
      color: ${({selected, disabled}) =>
        selected ? ColorsWIP.Blue700 : disabled ? ColorsWIP.Gray300 : ColorsWIP.Blue700};
    }
    ${IconWrapper} {
      color: ${({selected, disabled}) =>
        selected ? ColorsWIP.Blue700 : disabled ? ColorsWIP.Gray300 : ''};
    }
  }
`;

export const Count = styled.div`
  display: inline;
  font-family: ${FontFamily.monospace};
  font-size: 14px;
  font-weight: 500;
  letter-spacing: -0.02%;
  padding: 0 4px;
  color: ${ColorsWIP.Gray900};
  background: ${ColorsWIP.Gray100};
`;