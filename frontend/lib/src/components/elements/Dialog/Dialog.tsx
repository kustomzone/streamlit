/**
 * Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React, {
  ReactElement,
  ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react"

import { SIZE } from "baseui/modal"

import Modal, {
  ModalHeader,
  ModalBody,
} from "@streamlit/lib/src/components/shared/Modal"
import { notNullOrUndefined } from "@streamlit/lib/src/util/utils"
import { Block as BlockProto } from "@streamlit/lib/src/proto"
import { LibContext } from "@streamlit/lib/src/components/core/LibContext"
import ThemeProvider from "@streamlit/lib/src/components/core/ThemeProvider"
import IsSidebarContext from "@streamlit/lib/src/components/core/IsSidebarContext"

export interface Props {
  element: BlockProto.Dialog
}

const DIALOG_WIDTH = {
  small: "default",
  large: "60vw",
}

function parseWidthConfig(width?: string): string {
  if (width === undefined) {
    return SIZE.default
  }

  if (!isNaN(Number(width))) {
    return `${width}vw`
  }

  return DIALOG_WIDTH[width as keyof typeof DIALOG_WIDTH] ?? SIZE.default
}

const Dialog: React.FC<React.PropsWithChildren<Props>> = ({
  element,
  children,
}): ReactElement => {
  const { title, dismissible, width, isOpen: initialIsOpen } = element
  const [isOpen, setIsOpen] = useState<boolean>(initialIsOpen ?? false)
  useEffect(() => {
    // Only apply the expanded state if it was actually set in the proto.
    if (notNullOrUndefined(initialIsOpen)) {
      setIsOpen(initialIsOpen)
    }
  }, [initialIsOpen])

  const { activeTheme } = React.useContext(LibContext)
  const isInSidebar = React.useContext(IsSidebarContext)

  const ThemedModal = useMemo(() => {
    return function ThemedModal({ children }: { children: ReactNode }) {
      if (isInSidebar) {
        return (
          <ThemeProvider
            theme={activeTheme.emotion}
            baseuiTheme={activeTheme.basewebTheme}
          >
            {children}
          </ThemeProvider>
        )
      }

      return <>{children}</>
    }
  }, [activeTheme.emotion, activeTheme.basewebTheme, isInSidebar])

  return (
    <ThemedModal>
      <Modal
        isOpen={isOpen}
        closeable={dismissible}
        onClose={() => setIsOpen(false)}
        size={parseWidthConfig(width ?? SIZE.default)}
        overrides={{
          Dialog: {
            style: {
              // make sure the modal is not too small on mobile
              minWidth: "20rem",
            },
          },
        }}
      >
        <ModalHeader>{title}</ModalHeader>
        <ModalBody>{children}</ModalBody>
      </Modal>
    </ThemedModal>
  )
}

export default Dialog
