import Modal from './Modal'
import { Button } from './ui'

export default function Confirm({ open, title = '操作确认', text, okText = '确认', danger, onOk, onCancel }) {
  return (
    <Modal
      open={open}
      title={title}
      onClose={onCancel}
      footer={<>
        <Button variant="ghost" onClick={onCancel}>取消</Button>
        <Button variant={danger ? 'danger' : 'primary'} onClick={onOk}>{okText}</Button>
      </>}
    >
      <p>{text}</p>
    </Modal>
  )
}
