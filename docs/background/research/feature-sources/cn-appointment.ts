import type { AppointmentDraft, CaptchaChallenge } from "../types.js";
import { maskMobile } from "../utils/mask.js";

export type AppointmentNextField =
  | "slot"
  | "patient"
  | "mobile"
  | "captchaCode"
  | "smsCode"
  | "confirm"
  | "ready";

export function nextAppointmentField(draft: AppointmentDraft): AppointmentNextField {
  if (!draft.slot) return "slot";
  if (!draft.patient) return "patient";
  if (!draft.mobile) return "mobile";
  if (!draft.captcha) return "captchaCode";
  if (!draft.captchaCode) return "captchaCode";
  if (!draft.smsCode) return "smsCode";
  if (!draft.confirmed) return "confirm";
  return "ready";
}

export function appointmentPrompt(field: AppointmentNextField, captcha?: CaptchaChallenge): string {
  switch (field) {
    case "slot":
      return "请选择预约时间编号。";
    case "patient":
      return "请选择就诊人编号。";
    case "mobile":
      return "请提供接收短信验证码的手机号；默认可使用就诊人绑定手机号。";
    case "captchaCode":
      return captcha ? "请查看验证码图片，并提供图形验证码。" : "需要先获取图形验证码。";
    case "smsCode":
      return "短信验证码已发送后，请提供手机短信验证码。";
    case "confirm":
      return "请确认挂号摘要，确认无误后调用 appointment_confirm。";
    case "ready":
      return "已确认，可以提交挂号。";
  }
}

export function buildReservationPayload(draft: AppointmentDraft): Record<string, unknown> {
  if (!draft.hospital || !draft.department || !draft.expert || !draft.slot || !draft.patient) {
    throw new Error("预约信息不完整");
  }

  const raw = draft.slot.raw as Record<string, unknown>;
  const timeSegment = raw.timeSegment as Record<string, unknown> | undefined;
  const startTime = String(timeSegment?.startTime ?? draft.slot.startTime ?? "");
  const endTime = String(timeSegment?.endTime ?? draft.slot.endTime ?? "");
  const orderTime =
    startTime && endTime
      ? `${startTime.slice(0, 10)} ${startTime.slice(11, 16)}-${endTime.slice(11, 16)}`
      : `${draft.slot.date} ${draft.slot.timeRange === "1" ? "上午" : "下午"}`;

  return {
    deptName: draft.department.name,
    hosDeptCode: draft.department.hosDeptCode,
    doctName: draft.expert.doctName,
    hosDoctCode: draft.expert.hosDoctCode || "",
    platformHosNo: draft.hospital.hosOrgCode,
    hosOrgCode:
      draft.hospital.platformHosNo && draft.hospital.platformHosNo !== "-1"
        ? draft.hospital.platformHosNo
        : draft.hospital.hosOrgCode,
    hosOrgName: draft.hospital.name,
    memberId: draft.patient.memberId,
    numSourceId: draft.slot.numSourceId,
    orderTime,
    scheduleId: draft.slot.scheduleId,
    validateCode: draft.smsCode,
    visitCost: draft.slot.visitCost,
    visitLevelCode: String((draft.slot.raw as Record<string, unknown>).visitLevelCode ?? "")
  };
}

export function summarizeAppointment(draft: AppointmentDraft): Record<string, unknown> {
  return {
    hospital: draft.hospital?.name,
    department: draft.department?.name,
    expert: draft.expert?.doctName,
    visitLevel: draft.expert?.visitLevel,
    date: draft.slot?.date,
    time:
      draft.slot?.startTime && draft.slot.endTime
        ? `${draft.slot.startTime.slice(11, 16)}-${draft.slot.endTime.slice(11, 16)}`
        : draft.slot?.timeRange === "1"
          ? "上午"
          : draft.slot?.timeRange === "2"
            ? "下午"
            : draft.slot?.timeRange,
    visitCost: draft.slot?.visitCost,
    patient: draft.patient?.userName,
    patientMobile: draft.patient?.maskedMobile ?? maskMobile(draft.mobile),
    confirmed: Boolean(draft.confirmed)
  };
}

